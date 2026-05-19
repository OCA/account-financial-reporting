#  Copyright 2021 Simone Rubino - Agile Business Group
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase, tagged
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, test_reports


@tagged("post_install", "-at_install")
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
        # Check that report is produced correctly
        cls.wizard_with_line_details = cls.wizard_model.create(
            {
                "show_move_line_details": True,
                "receivable_accounts_only": True,
            }
        )
        cls.wizard_without_line_details = cls.wizard_model.create(
            {
                "show_move_line_details": False,
                "receivable_accounts_only": True,
            }
        )
        cls.account_age_report_config = cls.env[
            "account.age.report.configuration"
        ].create(
            {
                "name": "Intervals configuration",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "1-30",
                            "inferior_limit": 30,
                        },
                    ),
                ],
            }
        )

    def test_report_without_aged_report_configuration(self):
        """Check that report is produced correctly."""
        wizard = self.wizard_with_line_details
        wizard.onchange_type_accounts_only()
        data = wizard._prepare_report_data()

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
        second_wizard = self.wizard_without_line_details
        second_wizard.onchange_type_accounts_only()
        data = second_wizard._prepare_report_data()

        # Simulate web client behavior:
        # default value is a datetime.date but web client sends back strings
        data.update({"date_at": data["date_at"].strftime(DEFAULT_SERVER_DATE_FORMAT)})
        result = test_reports.try_report(
            self.env.cr,
            self.env.uid,
            "account_financial_report.aged_partner_balance",
            second_wizard.ids,
            data=data,
        )
        self.assertTrue(result)

    def test_report_with_aged_report_configuration(self):
        """Check that report is produced correctly."""
        wizard = self.wizard_with_line_details
        wizard.age_partner_config_id = self.account_age_report_config.id

        wizard.onchange_type_accounts_only()
        data = wizard._prepare_report_data()

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

        second_wizard = self.wizard_without_line_details
        second_wizard.age_partner_config_id = self.account_age_report_config.id

        second_wizard.onchange_type_accounts_only()
        data = second_wizard._prepare_report_data()

        # Simulate web client behavior:
        # default value is a datetime.date but web client sends back strings
        data.update({"date_at": data["date_at"].strftime(DEFAULT_SERVER_DATE_FORMAT)})
        result = test_reports.try_report(
            self.env.cr,
            self.env.uid,
            "account_financial_report.aged_partner_balance",
            second_wizard.ids,
            data=data,
        )
        self.assertTrue(result)

    def test_branch_company(self):
        """Aged partner balance for a branch must include parent company accounts."""
        parent = self.env.company
        branch = self.env["res.company"].create(
            {"name": "Aged Partner Branch", "parent_id": parent.id}
        )
        parent_account = self.env["account.account"].search(
            [("company_ids", "in", [parent.id]), ("reconcile", "=", True)],
            limit=1,
        )
        self.assertTrue(parent_account)
        self.assertNotIn(branch, parent_account.company_ids)
        wizard = self.wizard_model.create({"company_id": branch.id})
        res = wizard.onchange_company_id()
        accounts_in_domain = self.env["account.account"].search(
            res["domain"]["account_ids"]
        )
        self.assertIn(parent_account, accounts_in_domain)
