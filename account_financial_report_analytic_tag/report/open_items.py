# Copyright 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime

from odoo import models


class OpenItemsReport(models.AbstractModel):
    _inherit = "report.account_financial_report.open_items"

    def _get_ml_fields(self):
        # analytic_tag_ids is needed for the tags column.
        return super()._get_ml_fields() + ["analytic_tag_ids"]

    def _iter_open_items_lines(self, open_items):
        """Walk the Open_Items dict regardless of partner-grouping layout.

        Without partners: {acc_id: [line, ...]}
        With partners:    {acc_id: {prt_id: [line, ...]}}
        """
        for value in open_items.values():
            if isinstance(value, list):
                yield from value
            else:
                for ml_list in value.values():
                    if isinstance(ml_list, list):
                        yield from ml_list

    def _get_report_values(self, docids, data):
        # Normalize date fields to strings so the base module's
        # strptime() works regardless of the input type.
        for date_key in ("date_at", "date_from"):
            if isinstance(data.get(date_key), datetime.date | datetime.datetime):
                data[date_key] = data[date_key].strftime("%Y-%m-%d")
        res = super()._get_report_values(docids, data)
        if not data.get("show_analytic_tags"):
            return res
        # Gather all tag IDs up front so we can fetch names in one query.
        tag_ids = set()
        for ml in self._iter_open_items_lines(res["Open_Items"]):
            tag_ids.update(ml.get("analytic_tag_ids") or [])
        tags_data = self._get_tags_data(tag_ids)
        # Swap analytic_tag_ids → tag_ids and populate tag_display.
        for ml in self._iter_open_items_lines(res["Open_Items"]):
            ids = ml.pop("analytic_tag_ids", []) or []
            ml["tag_ids"] = ids
            ml["tag_display"] = self._build_tag_display(ids, tags_data)
        # Tags column is 4.75% wide; shrink both label columns to compensate.
        for style_key in ("ref_label_style", "ref_label_cumul_style"):
            current = res.get(style_key, "width: 0%;")
            current_w = float(current.replace("width:", "").replace("%;", "").strip())
            res[style_key] = f"width: {round(current_w - 4.75, 2)}%;"
        res["show_analytic_tags"] = True
        return res
