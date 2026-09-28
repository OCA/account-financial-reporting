# Copyright 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class JournalLedgerXlsx(models.AbstractModel):
    _inherit = "report.a_f_r.report_journal_ledger_xlsx"

    def _get_report_columns(self, report):
        columns = super()._get_report_columns(report)
        if not report.show_analytic_tags:
            return columns
        # Place the tags column after analytic distribution when present,
        # otherwise after the label column.
        col_list = list(columns.values())
        ref_col = next(
            (i for i, c in enumerate(col_list) if c.get("field") == "analytic_display"),
            None,
        )
        if ref_col is None:
            ref_col = next(
                (i for i, c in enumerate(col_list) if c.get("field") == "label"),
                len(col_list) - 1,
            )
        col_list.insert(
            ref_col + 1,
            {"header": _("Analytic Tags"), "field": "tag_display", "width": 20},
        )
        return {i: col for i, col in enumerate(col_list)}
