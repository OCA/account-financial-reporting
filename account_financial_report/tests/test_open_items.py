# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime

from odoo.tests import tagged
from odoo.tools import test_reports

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestOpenItems(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

    def setUp(self):
        super().setUp()
        self.wizard_model = self.env["open.items.report.wizard"]

    def test_partner_filter(self):
        partner_1 = self.env.ref("base.res_partner_1")
        partner_2 = self.env.ref("base.res_partner_2")
        partner_3 = self.env.ref("base.res_partner_3")
        partner_4 = self.env.ref("base.res_partner_4")
        partner_1.write({"is_company": False, "parent_id": partner_2.id})
        partner_3.write({"is_company": False})

        expected_list = [partner_2.id, partner_3.id, partner_4.id]
        context = {
            "active_ids": [partner_1.id, partner_2.id, partner_3.id, partner_4.id],
            "active_model": "res.partner",
        }

        wizard = self.env["open.items.report.wizard"].with_context(context)
        self.assertEqual(wizard._default_partners(), expected_list)

    def test_report(self):
        """Check that report is produced correctly."""
        date_at = (datetime.date.today() - datetime.timedelta(days=2)).strftime(
            "%Y-%m-%d"
        )
        wizard = self.wizard_model.create(
            {
                "show_partner_details": True,
                "receivable_accounts_only": True,
                "date_at": date_at,
            }
        )
        wizard.onchange_type_accounts_only()
        data = wizard._prepare_report_open_items()

        result = test_reports.try_report(
            self.env.cr,
            self.env.uid,
            "account_financial_report.open_items",
            wizard.ids,
            data=data,
        )
        self.assertTrue(result)

    def test_with_refund(self):
        """Check that report with refunds is produced correctly."""
        partner_1 = self.env.ref("base.res_partner_1")
        invoice_date = datetime.date.today() - datetime.timedelta(days=31)
        invoices = self.env["account.move"].create(
            [
                {
                    "move_type": "out_refund",
                    "partner_id": partner_1.id,
                    "invoice_date": invoice_date,
                    "invoice_line_ids": [
                        (
                            0,
                            None,
                            {
                                "quantity": 1,
                                "price_unit": 100,
                            },
                        ),
                    ],
                }
            ]
        )
        invoices.action_post()
        self.test_report()
