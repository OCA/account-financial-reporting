from datetime import date

from .common import PartnerStatementXlsxCommon


class TestDetailedActivityStatementXslx(PartnerStatementXlsxCommon):
    report_model_name = "report.p_s.report_detailed_activity_statement_xlsx"

    def setUp(self):
        super().setUp()
        # Customize lines for this report
        partner_id = self.partner.id
        currency_id = self.currency.id
        self.data["data"][partner_id]["currencies"][currency_id] = {
            "prior_lines": [
                {
                    "move_id": "PRIOR/001",
                    "date": date(2025, 11, 15),
                    "date_maturity": date(2025, 11, 30),
                    "name": "Prior Invoice",
                    "ref": "PRIOR1",
                    "amount": 200.0,
                    "open_amount": 50.0,
                    "balance": 150.0,
                    "reconciled_line": False,
                }
            ],
            "lines": [
                {
                    "move_id": "INV/001",
                    "date": date(2025, 12, 1),
                    "date_maturity": date(2025, 12, 31),
                    "name": "Current Invoice",
                    "ref": "CURR1",
                    "amount": 100.0,
                    "applied_amount": 20.0,
                    "open_amount": 80.0,
                    "balance": 80.0,
                    "reconciled_line": False,
                }
            ],
            "ending_lines": [
                {
                    "move_id": "END/001",
                    "date": date(2025, 12, 5),
                    "date_maturity": date(2025, 12, 31),
                    "name": "Ending Invoice",
                    "ref": "END1",
                    "amount": 50.0,
                    "open_amount": 50.0,
                    "balance": 50.0,
                    "reconciled_line": False,
                }
            ],
            "balance_forward": 150.0,
            "amount_due": 80.0,
        }

    def test_get_report_name_with_company(self):
        """Test that the report name includes the company and its currency."""
        report_name = self.report_model._get_report_name(self.report_model, self.data)
        self.assertIn(
            "Detailed Activity Statement",
            report_name,
            "Report name should include 'Detailed Activity Statement'.",
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

    def test_write_currency_prior_lines(self):
        """Test writing prior currency lines to the sheet."""
        row_pos = 0
        row_pos = self.report_model._write_currency_prior_lines(
            row_pos, self.sheet, self.partner, self.currency, self.data
        )
        self.assertTrue(
            self.sheet.write.called,
            "Prior currency lines were not written to the sheet.",
        )
        self.assertTrue(
            self.sheet.merge_range.called,
            "Prior currency lines were not merged correctly.",
        )

    def test_write_currency_lines(self):
        """Test writing currency lines to the sheet."""
        row_pos = 0
        row_pos = self.report_model._write_currency_lines(
            row_pos, self.sheet, self.partner, self.currency, self.data
        )
        self.assertTrue(
            self.sheet.write.called, "Currency lines were not written to the sheet."
        )
        self.assertTrue(
            self.sheet.merge_range.called, "Currency lines were not merged correctly."
        )

    def test_write_currency_ending_lines(self):
        """Test writing ending currency lines to the sheet."""
        row_pos = 0
        row_pos = self.report_model._write_currency_ending_lines(
            row_pos, self.sheet, self.partner, self.currency, self.data
        )
        self.assertTrue(
            self.sheet.write.called,
            "Ending currency lines were not written to the sheet.",
        )
        self.assertTrue(
            self.sheet.merge_range.called,
            "Ending currency lines were not merged correctly.",
        )

    def test_generate_xlsx_report(self):
        """Test the full XLSX report generation."""
        self.report_model.generate_xlsx_report(
            self.workbook, self.data, self.env["res.partner"].browse([self.partner.id])
        )
        (
            self.workbook.add_worksheet.assert_called(),
            "Worksheet was not added to the workbook.",
        )
        (
            self.sheet.set_landscape.assert_called(),
            "Landscape mode was not set for the sheet.",
        )
        self.assertTrue(
            self.sheet.merge_range.called,
            "Currency lines were not merged in the sheet.",
        )
        self.assertTrue(self.sheet.write.called, "Data was not written to the sheet.")
