# Copyright 2018 ForgeFlow, S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import new_test_user
from odoo.tests.common import TransactionCase


class TestOutstandingStatement(TransactionCase):
    """Tests for Outstanding Statement."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.res_users_model = cls.env["res.users"]
        cls.company = cls.env.ref("base.main_company")
        cls.company.external_report_layout_id = cls.env.ref(
            "web.external_layout_standard"
        )
        cls.partner1 = cls.env.ref("base.res_partner_2")
        cls.partner2 = cls.env.ref("base.res_partner_3")
        cls.user = new_test_user(
            cls.env, login="user_1", groups="account.group_account_user"
        )
        cls.statement_model = cls.env["report.partner_statement.outstanding_statement"]
        cls.wiz = cls.env["outstanding.statement.wizard"]
        cls.report_name = "partner_statement.outstanding_statement"
        cls.report_name_xlsx = "p_s.report_outstanding_statement_xlsx"
        cls.report_title = "Outstanding Statement"

    def test_customer_outstanding_statement(self):

        wiz_id = self.wiz.with_context(
            active_ids=[self.partner1.id, self.partner2.id]
        ).create({})
        wiz_id.aging_type = "months"

        statement = wiz_id.button_export_pdf()

        self.assertDictEqual(
            statement,
            {
                **{
                    "type": "ir.actions.report",
                    "report_name": self.report_name,
                    "report_type": "qweb-pdf",
                },
                **statement,
            },
            "There was an error and the PDF report was not generated.",
        )

        statement_xlsx = wiz_id.button_export_xlsx()

        self.assertDictEqual(
            statement_xlsx,
            {
                **{
                    "type": "ir.actions.report",
                    "report_name": self.report_name_xlsx,
                    "report_type": "xlsx",
                },
                **statement_xlsx,
            },
            "There was an error and the PDF report was not generated.",
        )

        data = wiz_id._prepare_statement()
        docids = data["partner_ids"]
        report = self.statement_model._get_report_values(docids, data)
        self.assertIsInstance(
            report, dict, "There was an error while compiling the report."
        )
        self.assertIn(
            "bucket_labels", report, "There was an error while compiling the report."
        )

    def test_customer_outstanding_report_no_wizard(self):
        docids = [self.partner1.id]
        report = self.statement_model._get_report_values(docids, False)
        self.assertIsInstance(
            report, dict, "There was an error while compiling the report."
        )
        self.assertIn(
            "bucket_labels", report, "There was an error while compiling the report."
        )

    def test_exclude_accounts(self):
        """Accounts can be excluded with a code selector."""
        # Arrange
        partners = self.partner1 | self.partner2
        wizard = self.wiz.with_context(
            active_ids=partners.ids,
        ).create({})

        # Edit one invoice
        # including a new account
        # that will be the only one not excluded
        partner_invoice = self.env["account.move"].search(
            [
                ("partner_id", "in", partners.ids),
                ("state", "=", "posted"),
            ],
            limit=1,
        )
        account = partner_invoice.line_ids.account_id.filtered(
            lambda a: a.internal_type == wizard.account_type
        )
        copy_account = account.copy()
        partner_invoice.line_ids.filtered(
            lambda l: l.account_id == account
        ).account_id = copy_account

        wizard_accounts = self.env["account.account"].search(
            [
                ("id", "!=", copy_account.id),
                ("internal_type", "=", wizard.account_type),
            ],
        )
        wizard.excluded_accounts_selector = ", ".join(
            [account.code for account in wizard_accounts]
        )
        # pre-condition
        self.assertTrue(wizard.excluded_accounts_selector)

        # Act
        data = wizard._prepare_statement()
        report = self.statement_model._get_report_values(partners.ids, data)

        # Assert
        # Only the new invoice is shown
        invoice_partner = partner_invoice.partner_id
        invoice_partner_data = report["data"][invoice_partner.id]["currencies"]
        invoice_partner_move_lines = invoice_partner_data[
            partner_invoice.currency_id.id
        ]["lines"]
        self.assertEqual(len(invoice_partner_move_lines), 1)
        self.assertEqual(invoice_partner_move_lines[0]["name"], partner_invoice.name)

        other_partner = partners - invoice_partner
        other_partner_data = report["data"].get(other_partner.id)
        self.assertFalse(other_partner_data)
