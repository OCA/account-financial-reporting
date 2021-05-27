# Copyright 2009-2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAmlReportXlsx(TransactionCase):
    def setUp(self):
        super(TestAmlReportXlsx, self).setUp()
        self.report = self.env.ref(
            "account_move_line_report_xls.action_account_move_line_xlsx"
        )
        sale_journal = self.env["account.journal"].search([("type", "=", "sale")])[0]
        ar = self.env["account.account"].search([("internal_type", "=", "receivable")])[
            0
        ]
        aml_vals = [
            {"name": "debit", "debit": 100, "account_id": ar.id},
            {"name": "credit", "credit": 100, "account_id": ar.id},
        ]
        am = self.env["account.move"].create(
            {
                "name": "test",
                "journal_id": sale_journal.id,
                "line_ids": [(0, 0, x) for x in aml_vals],
            }
        )
        self.amls = am.line_ids

    def test_aml_report_xlsx(self):
        report_xls = self.report._render_xlsx(self.amls.ids, None)
        self.assertEqual(report_xls[1], "xlsx")
