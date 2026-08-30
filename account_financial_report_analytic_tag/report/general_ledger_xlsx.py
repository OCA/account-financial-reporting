# Copyright 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class GeneralLedgerXlsx(models.AbstractModel):
    _inherit = "report.a_f_r.report_general_ledger_xlsx"

    def _get_report_columns(self, report):
        res = super()._get_report_columns(report)
        if not report.show_analytic_tags:
            return res

        # The base returns a plain dict keyed by sequential integers, so we
        # convert to a list, splice in the new column, then re-index.
        columns = list(res.values())
        analytic_dist_idx = next(
            (
                i
                for i, col in enumerate(columns)
                if col.get("field") == "analytic_distribution"
            ),
            None,
        )
        tag_col = {
            "header": _("Analytic Tags"),
            "field": "tag_display",
            "width": 20,
        }
        if analytic_dist_idx is not None:
            columns.insert(analytic_dist_idx + 1, tag_col)
        else:
            # No analytic distribution column — fall back to inserting after ref_label.
            ref_label_idx = next(
                (i for i, col in enumerate(columns) if col.get("field") == "ref_label"),
                len(columns) - 1,
            )
            columns.insert(ref_label_idx + 1, tag_col)
        return {i: col for i, col in enumerate(columns)}
