from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase

from ..report.report_statement_common import ReportStatementCommon


class TestReportStatementCommon(TransactionCase):
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
        cls.partner1 = cls.env["res.partner"].create({"name": "Partner 1"})
        cls.partner2 = cls.env["res.partner"].create({"name": "Partner 2"})
        cls.company = cls.env.company
        cls.statement = cls.env["statement.common"]
        cls.date_start = fields.Date.to_date("2025-01-01")
        cls.date_end = fields.Date.to_date("2025-01-31")

    def _mock_account_methods(self):
        """Patch abstract methods for _get_report_values with sample data."""
        prior_lines = {
            self.partner1.id: [
                {
                    "currency_id": 1,
                    "open_amount": 10.0,
                    "date": self.date_start,
                    "date_maturity": self.date_end,
                }
            ],
            self.partner2.id: [
                {
                    "currency_id": 1,
                    "open_amount": -5.0,
                    "date": self.date_start,
                    "date_maturity": self.date_end,
                }
            ],
        }
        lines = {
            self.partner1.id: [
                {
                    "currency_id": 1,
                    "amount": 20.0,
                    "ids": [],
                    "date": self.date_start,
                    "date_maturity": self.date_end,
                }
            ],
            self.partner2.id: [
                {
                    "currency_id": 1,
                    "amount": -10.0,
                    "ids": [],
                    "date": self.date_start,
                    "date_maturity": self.date_end,
                }
            ],
        }
        ending_lines = {
            self.partner1.id: [
                {
                    "currency_id": 1,
                    "open_amount": 5.0,
                    "date": self.date_end,
                    "date_maturity": self.date_end,
                }
            ],
            self.partner2.id: [
                {
                    "currency_id": 1,
                    "open_amount": -2.0,
                    "date": self.date_end,
                    "date_maturity": self.date_end,
                }
            ],
        }
        reconciled_lines = [
            {
                "id": 1,
                "date": self.date_start,
                "open_amount": 5.0,
                "amount": 5.0,
                "ids": [],
            }
        ]
        balances_forward = {
            self.partner1.id: [{"currency_id": 1, "balance": 100.0}],
            self.partner2.id: [{"currency_id": 1, "balance": -50.0}],
        }
        buckets = {
            self.partner1.id: [{"currency_id": 1, "current": 10}],
            self.partner2.id: [{"currency_id": 1, "current": -5}],
        }

        patcher_prior = patch.object(
            ReportStatementCommon,
            "_get_account_display_prior_lines",
            return_value=prior_lines,
        )
        patcher_lines = patch.object(
            ReportStatementCommon, "_get_account_display_lines", return_value=lines
        )
        patcher_ending = patch.object(
            ReportStatementCommon,
            "_get_account_display_ending_lines",
            return_value=ending_lines,
        )
        patcher_reconciled = patch.object(
            ReportStatementCommon,
            "_get_account_display_reconciled_lines",
            return_value=reconciled_lines,
        )
        patcher_initial = patch.object(
            ReportStatementCommon,
            "_get_account_initial_balance",
            return_value=balances_forward,
        )
        patcher_buckets = patch.object(
            ReportStatementCommon, "_get_account_show_buckets", return_value=buckets
        )

        return (
            patcher_prior,
            patcher_lines,
            patcher_ending,
            patcher_reconciled,
            patcher_initial,
            patcher_buckets,
        )

    def test_get_report_values_full_branches(self):
        """
        Test all missing lines by using realistic non-empty data
        and multiple partners.
        """
        (
            patcher_prior,
            patcher_lines,
            patcher_ending,
            patcher_reconciled,
            patcher_initial,
            patcher_buckets,
        ) = self._mock_account_methods()
        with (
            patcher_prior,
            patcher_lines,
            patcher_ending,
            patcher_reconciled,
            patcher_initial,
            patcher_buckets,
        ):
            data = {
                "company_id": self.company.id,
                "partner_ids": [self.partner1.id, self.partner2.id],
                "date_start": self.date_start.strftime("%Y-%m-%d"),
                "date_end": self.date_end.strftime("%Y-%m-%d"),
                "account_type": "asset_receivable",
                "excluded_accounts_ids": [],
                "show_only_overdue": False,
                "aging_type": "days",
                "is_detailed": True,
                "is_activity": True,
                "show_aging_buckets": True,
                "filter_non_due_partners": True,
                "filter_negative_balances": True,
            }

            res = self.statement._get_report_values(
                [self.partner1.id, self.partner2.id], data
            )

            # partner1 should remain, partner2 removed by filters
            self.assertIn(
                self.partner1.id, res["data"], "Partner1 should be in the report data."
            )
            self.assertNotIn(
                self.partner2.id,
                res["data"],
                "Partner2 should be excluded from the report data due to filters.",
            )
