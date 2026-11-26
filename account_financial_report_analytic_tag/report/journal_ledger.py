# Copyright 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime

from odoo import models


class JournalLedgerReport(models.AbstractModel):
    _inherit = "report.account_financial_report.journal_ledger"

    def _get_move_lines_data(self, ml, wizard, ml_taxes, auto_sequence, exigible):
        # Stash tag IDs on the line dict here so we don't need another
        # ORM call when building the display strings later.
        res = super()._get_move_lines_data(
            ml, wizard, ml_taxes, auto_sequence, exigible
        )
        res["tag_ids"] = ml.analytic_tag_ids.ids
        return res

    def _get_report_values(self, docids, data):
        # Normalize date fields to strings so the base module's
        # strptime() works regardless of the input type.
        for date_key in ("date_from", "date_to"):
            if isinstance(data.get(date_key), datetime.date | datetime.datetime):
                data[date_key] = data[date_key].strftime("%Y-%m-%d")
        res = super()._get_report_values(docids, data)
        if not data.get("show_analytic_tags"):
            return res
        # Gather all tag IDs up front so we can fetch names in one query.
        tag_ids = set()
        for move_data in res["Moves"]:
            for ml in move_data["report_move_lines"]:
                tag_ids.update(ml.get("tag_ids") or [])
        tags_data = self._get_tags_data(tag_ids)
        # Add tag_display to every line.
        for move_data in res["Moves"]:
            for ml in move_data["report_move_lines"]:
                ml["tag_display"] = self._build_tag_display(
                    ml.get("tag_ids") or [], tags_data
                )
        # Tags column is 4.75% wide; adjust the label column to match.
        current = res.get("label_column_style", "width: 0%;")
        current_w = float(current.replace("width:", "").replace("%;", "").strip())
        res["label_column_style"] = f"width: {round(current_w - 4.75, 2)}%;"
        res["show_analytic_tags"] = True
        return res
