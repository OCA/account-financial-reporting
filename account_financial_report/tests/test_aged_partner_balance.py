#  Copyright 2021 Simone Rubino - Agile Business Group
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
from unittest.mock import patch

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

    def test_report_values_json_intervals(self):
        report = self.env["report.account_financial_report.aged_partner_balance"]
        configuration = self.account_age_report_config
        interval = configuration.line_ids[0]
        line = {"line_rec": self.env["account.move.line"], interval: 25.0}
        account = {interval: 25.0, "partners": [{interval: 25.0, "move_lines": [line]}]}
        values = {
            "company_name": self.env.company.name,
            "currency_name": self.env.company.currency_id.name,
            "date_at": "2026-01-01",
            "only_posted_moves": True,
            "show_move_lines_details": True,
            "age_partner_config": configuration,
            "aged_partner_balance": [account],
        }
        with patch.object(type(report), "_get_report_values", return_value=values):
            result = report.get_report_values([], {"company_id": self.env.company.id})
        json.dumps(result, default=str)
        key = str(interval.id)
        self.assertEqual(
            result["age_partner_config_lines"][0],
            {"id": interval.id, "name": interval.name},
        )
        converted = result["aged_partner_balance"][0]
        self.assertEqual(converted[key], 25.0)
        self.assertEqual(converted["partners"][0]["move_lines"][0][key], 25.0)
        self.assertIn("line_rec", converted["partners"][0]["move_lines"][0])
        self.assertIn(interval, account)
        self.assertIn("line_rec", line)
