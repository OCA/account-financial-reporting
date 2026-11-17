from datetime import date

from .common import FORMATS, PartnerStatementXlsxCommon


class TestActivityStatementXlsx(PartnerStatementXlsxCommon):
    report_model_name = "report.p_s.report_activity_statement_xlsx"

    def setUp(self):
        super().setUp()
        partner_id = self.partner.id
        currency_id = self.currency.id
        self.data["data"][partner_id]["currencies"][currency_id]["lines"] = [
            {
                "move_id": "INV001",
                "date": date(2025, 12, 2),
                "date_maturity": date(2025, 12, 31),
                "name": "Invoice December",
                "ref": "REF001",
                "amount": 150.0,
                "applied_amount": 30.0,
                "open_amount": 120.0,
            }
        ]

    def test_header_row_data(self):
        """Test that the header row contains 'Reference Number'."""
        rows = self.report_model._get_currency_header_row_data(
            self.partner, self.currency, self.data
        )
        self.assertTrue(
            any("Reference Number" in cell["args"][0] for cell in rows),
            "Header row does not contain 'Reference Number'.",
        )

    def test_subheader(self):
        """Test that the subheader row contains the correct date."""
        rows = self.report_model._get_currency_subheader_row_data(
            self.partner, self.currency, self.data
        )
        self.assertEqual(
            rows[0]["args"][0], date(2025, 11, 30), "Subheader row date is incorrect."
        )

    def test_footer_row_data(self):
        """Test that the footer row contains the correct final amount."""
        rows = self.report_model._get_currency_footer_row_data(
            self.partner, self.currency, self.data
        )
        self.assertEqual(
            rows[-1]["args"][0],
            120.0,
            "Footer row does not contain the correct final amount.",
        )

    def test_write_row_data(self):
        """Test that the row data is written correctly to the sheet."""
        row_data = [
            {
                "col_pos": 0,
                "sheet_func": "write",
                "args": ("Test", FORMATS["format_tcell_left"]),
            }
        ]
        self.report_model._write_row_data(self.sheet, 0, row_data)
        self.sheet.write.assert_called_once()
        self.assertTrue(
            self.sheet.write.called, "Row data was not written to the sheet."
        )

    def test_write_currency_lines(self):
        """Test that currency lines are written and merged correctly in the sheet."""
        row_pos = 0
        row_pos = self.report_model._write_currency_lines(
            row_pos, self.sheet, self.partner, self.currency, self.data
        )
        self.assertTrue(
            self.sheet.merge_range.called,
            "Currency lines were not merged correctly in the sheet.",
        )
        self.assertTrue(
            self.sheet.write.called, "Currency lines were not written to the sheet."
        )

    def test_write_currency_buckets(self):
        """Test that currency aging buckets are written correctly in the sheet."""
        row_pos = 0
        row_pos = self.report_model._write_currency_buckets(
            row_pos, self.sheet, self.partner, self.currency, self.data
        )
        self.assertTrue(
            self.sheet.write.called,
            "Currency aging buckets were not written to the sheet.",
        )

    def test_generate_xlsx_report(self):
        """Test the generation of the full XLSX report."""
        self.report_model.generate_xlsx_report(
            self.workbook, self.data, self.env["res.partner"].browse([self.partner.id])
        )

        self.workbook.add_worksheet.assert_called()
        self.sheet.set_landscape.assert_called()
        self.assertTrue(
            self.sheet.merge_range.called,
            "Currency lines were not merged in the report.",
        )
        self.assertTrue(
            self.sheet.write.called, "Data was not written to the report sheet."
        )
