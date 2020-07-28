# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.mis_builder.tests.test_mis_report_instance import TestMisReportInstance


class TestL10nNlMisReports(TestMisReportInstance):
    def test_l10n_nl_mis_reports(self):
        instance = self.env["mis.report.instance"].create(
            {
                "name": "Balance Sheet",
                "report_id": self.env.ref("l10n_nl_mis_reports.report_bs").id,
            }
        )
        result_dict = instance.compute()
        self.assertEqual(len(result_dict.get("horizontal_matrices", [])), 2)
