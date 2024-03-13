#  Copyright 2021 Simone Rubino - Agile Business Group
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, test_reports


class TestAgedPartnerBalance(TransactionCase):
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
        cls.wizard_model = cls.env["aged.partner.balance.report.wizard"]
        cls.account001 = cls.env["account.account"].create(
            {
                "code": "001",
                "name": "Account 001",
                "account_type": "income_other",
                "reconcile": True,
            }
        )

    def test_report(self):
        """Check that report is produced correctly."""
        wizard = self.wizard_model.create(
            {
                "show_move_line_details": True,
                "receivable_accounts_only": True,
            }
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

    def test_all_accounts_loaded(self):
        # Tests if all accounts are loaded when the account_code_ fields changed
        all_accounts = self.env["account.account"].search(
            [("reconcile", "=", True)], order="code"
        )
        aged_partner_balance = self.wizard_model.create(
            {
                "account_code_from": self.account001.id,
                "account_code_to": all_accounts[-1].id,
            }
        )
        aged_partner_balance.on_change_account_range()
        all_accounts_code_set = set()
        aged_partner_balance_code_set = set()
        [all_accounts_code_set.add(account.code) for account in all_accounts]
        [
            aged_partner_balance_code_set.add(account.code)
            for account in aged_partner_balance.account_ids
        ]
        self.assertEqual(len(aged_partner_balance_code_set), len(all_accounts_code_set))
        self.assertTrue(aged_partner_balance_code_set == all_accounts_code_set)
