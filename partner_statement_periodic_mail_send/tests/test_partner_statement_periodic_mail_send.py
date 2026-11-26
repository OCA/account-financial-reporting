# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date
from unittest.mock import patch

from freezegun import freeze_time

from odoo import Command, fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPartnerStatementPeriodicMailSend(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                tracking_disable=True,
            )
        )
        cls.ResPartner = cls.env["res.partner"]
        cls.partner = cls.ResPartner.create(
            {
                "name": "Test Customer",
                "email": "customer@example.com",
                "customer_rank": 1,
            }
        )
        cls.partner_no_email = cls.ResPartner.create(
            {
                "name": "Customer No Email",
                "customer_rank": 1,
            }
        )
        cls.partner_excluded = cls.ResPartner.create(
            {
                "name": "Excluded Customer",
                "email": "excluded@example.com",
                "customer_rank": 1,
                "exclude_periodic_statement": True,
            }
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Test Service",
                            "quantity": 1,
                            "price_unit": 500.0,
                        }
                    )
                ],
            }
        )
        cls.invoice.action_post()
        cls.date_start = date.today().replace(day=1)
        cls.date_end = date.today().replace(day=28)

    def _mock_render(self):
        return patch(
            "odoo.addons.base.models.ir_actions_report.IrActionsReport._render",
            return_value=(b"%PDF-fake", "pdf"),
        )

    def _mock_send(self):
        return patch("odoo.addons.mail.models.mail_mail.MailMail.send")

    def test_exclude_periodic_statement_field(self):
        self.assertFalse(self.partner.exclude_periodic_statement)
        self.assertTrue(self.partner_excluded.exclude_periodic_statement)

    def test_skip_partner_without_email(self):
        with self._mock_render(), self._mock_send():
            mails_before = self.env["mail.mail"].search_count([])
            self.partner_no_email._send_periodic_statement_mail(
                self.date_start, self.date_end
            )
            mails_after = self.env["mail.mail"].search_count([])
        self.assertEqual(mails_before, mails_after)

    def test_send_mail_with_attachment(self):
        with self._mock_render(), self._mock_send():
            self.partner._send_periodic_statement_mail(self.date_start, self.date_end)
        mail = self.env["mail.mail"].search(
            [("email_to", "=", self.partner.email)], limit=1
        )
        self.assertTrue(mail)
        self.assertTrue(mail.attachment_ids)
        self.assertIn("Statement_", mail.attachment_ids[0].name)
        self.assertEqual(self.partner.last_periodic_statement_date, self.date_end)

    def test_action_send_excludes_excluded_partner(self):
        sent_to = []

        def mock_send(rec, date_start, date_end):
            sent_to.append(rec.id)

        with patch.object(
            type(self.partner), "_send_periodic_statement_mail", mock_send
        ):
            self.partner._send_periodic_statement(
                date_start=self.date_start, date_end=self.date_end
            )
        self.assertNotIn(self.partner_excluded.id, sent_to)
        self.assertIn(self.partner.id, sent_to)

    @freeze_time("2026-06-15")
    def test_cron_skips_non_last_day(self):
        with self._mock_render():
            with patch.object(
                type(self.partner),
                "_send_periodic_statement",
            ) as mock_send:
                self.ResPartner._cron_send_periodic_statement()
                mock_send.assert_not_called()

    @freeze_time("2026-06-30")
    def test_cron_runs_on_last_day(self):
        with self._mock_render():
            with patch.object(
                type(self.partner),
                "_send_periodic_statement",
            ) as mock_send:
                self.ResPartner._cron_send_periodic_statement()
                mock_send.assert_called_once()
                call_kwargs = mock_send.call_args[1]
                self.assertEqual(call_kwargs["date_start"], date(2026, 6, 1))
                self.assertEqual(call_kwargs["date_end"], date(2026, 6, 30))

    @freeze_time("2026-06-15")
    def test_cron_runs_with_day_param(self):
        with self._mock_render():
            with patch.object(
                type(self.partner),
                "_send_periodic_statement",
            ) as mock_send:
                self.ResPartner._cron_send_periodic_statement(day=10)
                mock_send.assert_called_once()
                call_kwargs = mock_send.call_args[1]
                self.assertEqual(call_kwargs["date_start"], date(2026, 6, 1))
                self.assertEqual(call_kwargs["date_end"], date(2026, 6, 10))

    def test_get_periodic_statement_data(self):
        data = self.partner._get_periodic_statement_data(self.date_start, self.date_end)
        self.assertIn("partner_ids", data)
        self.assertIn(self.partner.id, data["partner_ids"])
        self.assertIn("company_id", data)
        self.assertEqual(data["date_start"], self.date_start)
        self.assertEqual(data["date_end"], self.date_end)
