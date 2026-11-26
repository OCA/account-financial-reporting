# Copyright 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime

from odoo import models


class GeneralLedgerReport(models.AbstractModel):
    _inherit = "report.account_financial_report.general_ledger"

    def _get_ml_fields(self):
        # analytic_tag_ids is needed for the tags column.
        return super()._get_ml_fields() + ["analytic_tag_ids"]

    def _get_move_line_data(self, move_line):
        # The base only copies fields it knows about, so analytic_tag_ids
        # would be silently dropped without this override.
        res = super()._get_move_line_data(move_line)
        res["analytic_tag_ids"] = move_line.get("analytic_tag_ids") or []
        return res

    def _iter_gl_move_lines(self, account):
        """Walk all move lines in an account, handling flat and grouped layouts."""
        if account.get("list_grouped"):
            for group in account["list_grouped"]:
                yield from group.get("move_lines", [])
        else:
            yield from account.get("move_lines", [])

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
        for account in res["general_ledger"]:
            for ml in self._iter_gl_move_lines(account):
                tag_ids.update(ml.get("analytic_tag_ids") or [])
        tags_data = self._get_tags_data(tag_ids)
        # Swap analytic_tag_ids → tag_ids and populate tag_display for XLSX.
        for account in res["general_ledger"]:
            for ml in self._iter_gl_move_lines(account):
                raw_ids = ml.pop("analytic_tag_ids", []) or []
                ml["tag_ids"] = raw_ids
                ml["tag_display"] = self._build_tag_display(raw_ids, tags_data)
        # The tags column is 4.75% wide; pull the ref-label back accordingly.
        current = res.get("ref_label_style", "width: 0%;")
        current_w = float(current.replace("width:", "").replace("%;", "").strip())
        res["ref_label_style"] = f"width: {round(current_w - 4.75, 2)}%;"
        res["show_analytic_tags"] = True
        res["tags_data"] = tags_data
        return res
