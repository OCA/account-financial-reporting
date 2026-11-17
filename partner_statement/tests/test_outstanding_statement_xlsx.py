from datetime import date
from unittest.mock import MagicMock

from .common import FORMATS, PartnerStatementXlsxCommon


class TestOutstandingStatementXlsx(PartnerStatementXlsxCommon):
    report_model_name = "report.p_s.report_outstanding_statement_xlsx"

    def setUp(self):
        super().setUp()
        self.partner_id = self.partner.id
        self.currency_id = self.currency.id
        self.data["data"][self.partner_id]["currencies"][self.currency_id]["lines"] = [
            {
                "move_id": "INV/2025/001",
                "date": date(2025, 12, 1),
                "date_maturity": date(2025, 12, 31),
                "name": "Invoice 1",
                "ref": "INV1",
                "amount": 100.0,
                "open_amount": 50.0,
                "balance": 50.0,
            }
        ]
        self.data["data"][self.partner_id]["currencies"][self.currency_id][
            "buckets"
        ] = {
            "current": 50.0,
            "b_1_30": 0.0,
            "b_30_60": 0.0,
            "b_60_90": 0.0,
            "b_90_120": 0.0,
            "b_over_120": 0.0,
            "balance": 50.0,
        }

    def test_get_report_name_with_company(self):
        """Test that the report name includes the company and its currency."""
        report_name = self.report_model._get_report_name(self.report_model, self.data)
        self.assertIn(
            "Outstanding Statement",
            report_name,
            "Report name should include 'Outstanding Statement'.",
        )
        self.assertIn(
            self.company.name,
            report_name,
            f"Report name should include company name: {self.company.name}.",
        )
        self.assertIn(
            self.company.currency_id.name,
            report_name,
            f"Report name should include company's currency: "
            f"{self.company.currency_id.name}.",
        )

    def test_get_currency_header_row_data(self):
        """Test the generation of the currency header row for the report."""
        header_data = self.report_model._get_currency_header_row_data(
            self.partner, self.currency, self.data
        )
        self.assertEqual(
            len(header_data), 7, "Currency header row should contain 7 columns."
        )
        self.assertEqual(
            header_data[0]["args"][0],
            "Reference Number",
            "First column should be 'Reference Number'.",
        )

    def test_get_currency_line_row_data(self):
        """Test the generation of data rows for currency lines in the report."""
        line = self.data["data"][self.partner.id]["currencies"][self.currency.id][
            "lines"
        ][0]
        line_data = self.report_model._get_currency_line_row_data(
            self.partner, self.currency, self.data, line
        )
        self.assertEqual(
            len(line_data), 7, "Currency line row should contain 7 columns."
        )
        self.assertEqual(
            line_data[0]["args"][0],
            "INV/2025/001",
            "First column should contain 'INV/2025/001'.",
        )
        self.assertEqual(
            line_data[4]["args"][0],
            100.0,
            "Fifth column should contain the amount '100.0'.",
        )

    def test_write_row_data_calls_sheet_methods(self):
        """Test that row data writing calls the appropriate sheet methods."""
        sheet_mock = MagicMock()
        row_data = [
            {
                "col_pos": 0,
                "sheet_func": "write",
                "args": ("Test", FORMATS["format_theader_yellow_center"]),
            },
            {
                "col_pos": 1,
                "sheet_func": "write",
                "args": (123, FORMATS["format_tcell_left"]),
            },
        ]
        self.report_model._write_row_data(sheet_mock, 0, row_data)
        self.assertEqual(
            sheet_mock.write.call_count, 2, "The 'write' method should be called twice."
        )
        sheet_mock.write.assert_any_call(
            0, 0, "Test", FORMATS["format_theader_yellow_center"]
        )
        sheet_mock.write.assert_any_call(0, 1, 123, FORMATS["format_tcell_left"])

    def test_write_currency_lines_and_buckets(self):
        """Test writing currency lines and aging buckets to sheet."""
        row_pos = 0
        # Test writing lines
        row_pos = self.report_model._write_currency_lines(
            row_pos, self.sheet, self.partner, self.currency, self.data
        )
        self.assertTrue(
            self.sheet.merge_range.called,
            "Currency lines should be merged in the sheet.",
        )
        self.assertTrue(
            self.sheet.write.called, "Currency lines should be written to the sheet."
        )

        # Test writing buckets
        row_pos = self.report_model._write_currency_buckets(
            row_pos, self.sheet, self.partner, self.currency, self.data
        )
        self.assertTrue(
            self.sheet.write.called,
            "Currency aging buckets should be written to the sheet.",
        )

    def test_generate_xlsx_report(self):
        """Test the full generation of the XLSX report."""
        self.report_model.generate_xlsx_report(
            self.workbook, self.data, self.env["res.partner"].browse([self.partner.id])
        )
        (
            self.workbook.add_worksheet.assert_called(),
            "Worksheet should be added to the workbook.",
        )
        (
            self.sheet.set_landscape.assert_called(),
            "Sheet should be set to landscape mode.",
        )
        self.assertTrue(
            self.sheet.merge_range.called,
            "Currency lines should be merged in the report.",
        )
        self.assertTrue(
            self.sheet.write.called, "Data should be written to the report sheet."
        )
