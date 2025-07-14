# Copyright 2009-2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class TestAmlReportXlsx(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_ref = "account_move_line_report_xls.action_account_move_line_xlsx"
        cls.report = cls.env.ref(
            "account_move_line_report_xls.action_account_move_line_xlsx"
        )
        sale_journal = cls.env["account.journal"].search([("type", "=", "sale")])[0]
        ar = cls.env["account.account"].search(
            [("account_type", "=", "asset_receivable")]
        )[0]
        aml_vals = [
            {"name": "debit", "debit": 100, "account_id": ar.id},
            {"name": "credit", "credit": 100, "account_id": ar.id},
        ]
        am = cls.env["account.move"].create(
            {
                "name": "test",
                "journal_id": sale_journal.id,
                "line_ids": [Command.create(x) for x in aml_vals],
            }
        )
        cls.amls = am.line_ids

    def test_aml_report_xlsx(self):
        report_xls = self.report._render_xlsx(self.report_ref, self.amls.ids, None)
        self.assertEqual(report_xls[1], "xlsx")
