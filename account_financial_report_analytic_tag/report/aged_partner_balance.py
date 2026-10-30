# Copyright 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime

from odoo import models


class AgedPartnerBalanceReport(models.AbstractModel):
    _inherit = "report.account_financial_report.aged_partner_balance"

    def _get_report_values(self, docids, data):
        # Normalize date fields to strings so the base module's
        # strptime() works regardless of the input type.
        for date_key in ("date_at", "date_from"):
            if isinstance(data.get(date_key), datetime.date | datetime.datetime):
                data[date_key] = data[date_key].strftime("%Y-%m-%d")
        res = super()._get_report_values(docids, data)
        show_move_line_details = data.get("show_move_line_details")
        if not data.get("show_analytic_tags") or not show_move_line_details:
            return res
        # Map move line IDs to their result dicts so we can batch the tag fetch.
        ml_id_to_dict = {}
        for account in res["aged_partner_balance"]:
            for partner in account.get("partners", []):
                for ml in partner.get("move_lines", []):
                    rec = ml.get("line_rec")
                    if rec:
                        ml_id_to_dict[rec.id] = ml
        if not ml_id_to_dict:
            return res
        tag_rows = self.env["account.move.line"].search_read(
            [("id", "in", list(ml_id_to_dict.keys()))],
            ["analytic_tag_ids"],
        )
        tag_ids = set()
        ml_tag_map = {}
        for row in tag_rows:
            ml_tag_map[row["id"]] = row["analytic_tag_ids"]
            tag_ids.update(row["analytic_tag_ids"])
        tags_data = self._get_tags_data(tag_ids)
        for ml_id, ml in ml_id_to_dict.items():
            ids = ml_tag_map.get(ml_id, [])
            ml["tag_ids"] = ids
            ml["tag_display"] = self._build_tag_display(ids, tags_data)
        # Tags column is 4.75% wide; pull both label columns back.
        for style_key in ("ref_label_style", "ref_label_cumul_partner_style"):
            current = res.get(style_key, "width: 0%;")
            current_w = float(current.replace("width:", "").replace("%;", "").strip())
            res[style_key] = f"width: {round(current_w - 4.75, 2)}%;"
        res["show_analytic_tags"] = True
        return res
