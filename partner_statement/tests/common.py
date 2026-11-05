from datetime import date
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import FORMATS


class PartnerStatementXlsxCommon(TransactionCase):
    report_model_name = None

    def setUp(self):
        super().setUp()
        self.env = self.env(
            context=dict(
                self.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        # Base objects
        self.company = self.env["res.company"].create(
            {
                "name": "Test Company",
                "currency_id": self.env.ref("base.USD").id,
            }
        )
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.currency = self.env.ref("base.USD")
        self.report_model = self.env[self.report_model_name]

        # Mock workbook and worksheet for report generation
        self.workbook = MagicMock()
        self.sheet = MagicMock()
        self.workbook.add_worksheet.return_value = self.sheet
        self.workbook.add_format.return_value = MagicMock()

        # Mock report formats
        self.FORMATS = {}
        for key in [
            "format_distributed",
            "current_money_format",
            "format_tcell_left",
            "format_tcell_date_left",
            "format_theader_yellow_center",
            "format_left_bold",
            "format_right_bold",
            "format_ws_title",
            "format_theader_yellow_right",
            "format_date_left",
            "format_left",
        ]:
            FORMATS[key] = MagicMock()

        # Initialize default report data
        today = date(2025, 12, 11)
        self.data = {
            "company_id": self.company.id,
            "partner_ids": [self.partner.id],
            "account_type": "asset_receivable",
            "excluded_accounts_ids": [],
            "show_only_overdue": False,
            "aging_type": "normal",
            "show_aging_buckets": True,
            "date_end": date(2025, 12, 31),
            "data": {
                self.partner.id: {
                    "start": date(2025, 12, 1),
                    "end": date(2025, 12, 31),
                    "prior_day": date(2025, 11, 30),
                    "today": today,
                    "currencies": {
                        self.currency.id: {
                            "balance_forward": 300.0,
                            "amount_due": 120.0,
                            "lines": [],
                            "buckets": {
                                "current": 120.0,
                                "b_1_30": 0.0,
                                "b_30_60": 0.0,
                                "b_60_90": 0.0,
                                "b_90_120": 0.0,
                                "b_over_120": 0.0,
                                "balance": 120.0,
                            },
                        }
                    },
                }
            },
            "get_title": lambda partner, *args, **kw: f"Statement {partner.name}",
        }

        # Patch method for getting aging bucket labels
        self.patcher = patch(
            "odoo.addons.partner_statement.report.report_statement_common.ReportStatementCommon._get_bucket_labels",
            return_value=[
                "Current",
                "1-30",
                "31-60",
                "61-90",
                "91-120",
                ">120",
                "Balance",
            ],
        )
        self.mock_bucket_labels = self.patcher.start()
        self.addCleanup(self.patcher.stop)
