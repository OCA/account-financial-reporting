# Copyright 2020 Hunki Enterprises BV
# Copyright 2021 Opener B.V. <stefan@opener.am>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestMisTemplateFinancialReport(TransactionCase):
    def test_mis_template_financial_report(self):
        instance = self.env["mis.report.instance"].create(
            {
                "name": "Balance Sheet",
                "report_id": self.env.ref("mis_template_financial_report.report_bs").id,
            }
        )
        self.assertTrue(instance.allow_horizontal)
        instance.horizontal = True
        result_dict = instance.compute()
        self.assertEqual(len(result_dict.get("split_matrices", [])), 2)
