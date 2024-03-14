#  Copyright 2021 Simone Rubino - Agile Business Group
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, TransactionCase
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, test_reports


class TestAgedPartnerBalance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.wizard_model = self.env["aged.partner.balance.report.wizard"]

    def test_report(self):
        """Check that report is produced correctly."""
        wizard = self.wizard_model.create(
            {"show_move_line_details": True, "receivable_accounts_only": True}
        )
        wizard.onchange_type_accounts_only()
        data = wizard._prepare_report_aged_partner_balance()

        # Simulate web client behavior:
        # default value is a datetime.date but web client sends back strings
        data.update({"date_at": data["date_at"].strftime(DEFAULT_SERVER_DATE_FORMAT)})
        result = test_reports.try_report(
            self.env.cr,
            self.env.uid,
            "account_financial_report.aged_partner_balance",
            wizard.ids,
            data=data,
        )
        self.assertTrue(result)

    def test_account_range_filter(self):
        account_cex001 = self.env["account.account"].create(
            {
                "code": "CEX001",
                "name": "Account CEX001",
                "user_type_id": self.env.ref(
                    "account.data_account_type_other_income"
                ).id,
                "reconcile": True,
            },
        )
        with Form(self.env["aged.partner.balance.report.wizard"]) as wizard_form:
            wizard_form.account_code_from = account_cex001
            self.assertEqual([a for a in wizard_form.account_ids], [])
            wizard_form.account_code_to = account_cex001
            self.assertEqual(
                [a.id for a in wizard_form.account_ids], account_cex001.ids
            )
