# Copyright 2026 Ledo Enterprises
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestMultiCompanyReports(AccountTestInvoicingCommon):
    """Test that financial reports render correctly in multi-company setups.

    In Odoo 18, account.code is a computed field backed by code_store (jsonb).
    Without the correct company context, account.code returns False for accounts
    belonging to other companies, causing TypeError in report generation.
    """

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
        cls.company_data_2 = cls.setup_other_company()
        cls.company_2 = cls.company_data_2["company"]
        cls.env.user.write({"company_ids": [(4, cls.company_2.id)]})

        # Create a posted journal entry in company 2 so reports have data
        journal_2 = cls.company_data_2["default_journal_misc"]
        account_revenue_2 = cls.company_data_2["default_account_revenue"]
        account_receivable_2 = cls.company_data_2["default_account_receivable"]

        move = (
            cls.env["account.move"]
            .with_company(cls.company_2)
            .create(
                {
                    "journal_id": journal_2.id,
                    "date": date(2025, 6, 15),
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "account_id": account_receivable_2.id,
                                "partner_id": cls.env["res.partner"]
                                .create({"name": "Test Partner MC"})
                                .id,
                                "debit": 1000.0,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": account_revenue_2.id,
                                "credit": 1000.0,
                            },
                        ),
                    ],
                }
            )
        )
        move.action_post()

        cls.fy_date_start = date(2025, 1, 1)
        cls.fy_date_end = date(2025, 12, 31)

    def _get_gl_report_data(self, company):
        """Generate General Ledger report data for the given company.

        env.company deliberately differs from the report's target company
        to reproduce the multi-company account.code resolution issue.
        """
        self.assertEqual(self.env.company, self.company_data["company"])
        wizard = self.env["general.ledger.report.wizard"].create(
            {
                "company_id": company.id,
                "date_from": self.fy_date_start,
                "date_to": self.fy_date_end,
                "target_move": "posted",
                "hide_account_at_0": True,
                "centralize": True,
            }
        )
        data = wizard._prepare_report_data()
        return self.env[
            "report.account_financial_report.general_ledger"
        ]._get_report_values(wizard, data)

    def _get_tb_report_data(self, company):
        """Generate Trial Balance report data for the given company."""
        self.assertEqual(self.env.company, self.company_data["company"])
        wizard = self.env["trial.balance.report.wizard"].create(
            {
                "company_id": company.id,
                "date_from": self.fy_date_start,
                "date_to": self.fy_date_end,
                "target_move": "posted",
                "hide_account_at_0": True,
            }
        )
        data = wizard._prepare_report_data()
        return self.env[
            "report.account_financial_report.trial_balance"
        ]._get_report_values(wizard, data)

    def _get_apb_report_data(self, company, receivable=True):
        """Generate Aged Partner Balance report data for the given company."""
        self.assertEqual(self.env.company, self.company_data["company"])
        wizard = self.env["aged.partner.balance.report.wizard"].create(
            {
                "company_id": company.id,
                "date_at": self.fy_date_end,
                "target_move": "posted",
                "receivable_accounts_only": receivable,
                "payable_accounts_only": not receivable,
            }
        )
        data = wizard._prepare_report_data()
        # Simulate web client behavior: the wizard default is a datetime.date
        # but the web client sends date_at back as a string, which the report's
        # _get_report_values feeds to datetime.strptime.
        data.update({"date_at": data["date_at"].strftime("%Y-%m-%d")})
        return self.env[
            "report.account_financial_report.aged_partner_balance"
        ]._get_report_values(wizard, data)

    def test_gl_multicompany(self):
        """General Ledger renders for non-default company without TypeError."""
        res = self._get_gl_report_data(self.company_2)
        self.assertIn("general_ledger", res)
        # Verify accounts_data has string codes, not False
        for acct_id, acct_data in res.get("accounts_data", {}).items():
            self.assertIsInstance(
                acct_data["code"],
                str,
                f"Account {acct_id} code should be str, got {type(acct_data['code'])}",
            )

    def test_tb_multicompany(self):
        """Trial Balance renders for non-default company without TypeError."""
        res = self._get_tb_report_data(self.company_2)
        self.assertIn("trial_balance", res)
        for acct_id, acct_data in res.get("accounts_data", {}).items():
            self.assertIsInstance(
                acct_data["code"],
                str,
                f"Account {acct_id} code should be str, got {type(acct_data['code'])}",
            )

    def test_apb_receivable_multicompany(self):
        """Aged Receivable renders for non-default company without TypeError."""
        res = self._get_apb_report_data(self.company_2, receivable=True)
        self.assertIn("aged_partner_balance", res)

    def test_apb_payable_multicompany(self):
        """Aged Payable renders for non-default company without TypeError."""
        res = self._get_apb_report_data(self.company_2, receivable=False)
        self.assertIn("aged_partner_balance", res)
