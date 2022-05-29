# Copyright 2022 APPSTOGROW
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestMisTemplateFinancialReportDetailed(TransactionCase):
    def test_mis_template_financial_report_detailed(self):
        (
            report_pl,
            report_bs,
            instance_pl,
            instance_bs,
        ) = self.env["mis.report"].generate_reports()

        self.assertEqual(
            report_pl.kpi_ids.filtered(lambda kpi: kpi.name == "pl").expression,
            "income + expense",
            "There is no kpi named 'pl' with the expression 'income + expense'",
        )
        self.assertTrue(instance_bs.comparison_mode)
