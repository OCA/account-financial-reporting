# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.mis_builder.tests.test_mis_report_instance import TestMisReportInstance


class TestMisTemplateFinancialReport(TestMisReportInstance):
    def test_mis_template_financial_report(self):
        instance = self.env["mis.report.instance"].create(
            {
                "name": "Balance Sheet",
                "report_id": self.env.ref("mis_template_financial_report.report_bs").id,
            }
        )
        result_dict = instance.compute()
        self.assertEqual(len(result_dict.get("horizontal_matrices", [])), 2)
