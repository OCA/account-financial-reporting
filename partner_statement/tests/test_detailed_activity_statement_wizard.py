from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase


class TestDetailedActivityStatementWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.wizard = (
            cls.env["detailed.activity.statement.wizard"]
            .with_context(active_ids=[cls.partner.id])
            .create(
                {
                    "show_aging_buckets": True,
                    "show_balance": True,
                }
            )
        )

    def test_prepare_statement_adds_is_detailed(self):
        """_prepare_statement should include 'is_detailed' = True"""
        result = self.wizard._prepare_statement()
        self.assertIn(
            "is_detailed", result, "'is_detailed' key is missing in the result."
        )
        self.assertTrue(result["is_detailed"], "'is_detailed' value should be True.")

    def test_print_report_pdf_calls_correct_report(self):
        """_print_report with pdf type should call correct report"""
        mock_report_action = MagicMock()
        with patch(
            "odoo.models.BaseModel.search",
            return_value=MagicMock(
                report_action=MagicMock(return_value=mock_report_action)
            ),
        ):
            action = self.wizard._print_report("pdf")
            self.assertEqual(
                action, mock_report_action, "PDF report action is incorrect."
            )

    def test_print_report_xlsx_calls_correct_report(self):
        """_print_report with xlsx type should call correct report"""
        mock_report_action = MagicMock()
        with patch(
            "odoo.models.BaseModel.search",
            return_value=MagicMock(
                report_action=MagicMock(return_value=mock_report_action)
            ),
        ) as mock_search:
            action = self.wizard._print_report("xlsx")
            self.assertEqual(
                action, mock_report_action, "XLSX report action is incorrect."
            )
            mock_search.assert_called()
