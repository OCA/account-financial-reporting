# Copyright 2024 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class OpenItemsReport(models.AbstractModel):
    _inherit = "report.account_financial_report.open_items"

    def _get_data(
        self,
        account_ids,
        partner_ids,
        date_at_object,
        only_posted_moves,
        company_id,
        date_from,
        grouped_by,
    ):
        (
            move_lines,
            partners_data,
            journals_data,
            accounts_data,
            open_items_move_lines_data,
        ) = super()._get_data(
            account_ids,
            partner_ids,
            date_at_object,
            only_posted_moves,
            company_id,
            date_from,
            grouped_by,
        )
        if grouped_by == "partner_shipping":
            for move_line in move_lines:
                move = self.env["account.move"].browse(move_line["move_id"][0])
                partner = move.partner_shipping_id
                group_id = partner.id or 0
                group_name = partner.display_name or _("Missing Delivery Address")
                if group_id not in partners_data:
                    partners_data[group_id] = {"id": group_id, "name": group_name}
                # Update move_line with partner_shipping
                move_line.update(
                    {
                        "partner_id": group_id,
                        "partner_name": group_name,
                    }
                )
                # Update open_items_move_lines_data
                acc_id = move_line["account_id"][0]
                if acc_id not in open_items_move_lines_data:
                    open_items_move_lines_data[acc_id] = {group_id: [move_line]}
                else:
                    if group_id not in open_items_move_lines_data[acc_id]:
                        open_items_move_lines_data[acc_id][group_id] = [move_line]
                    else:
                        open_items_move_lines_data[acc_id][group_id].append(move_line)
        return (
            move_lines,
            partners_data,
            journals_data,
            accounts_data,
            open_items_move_lines_data,
        )
