# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountAccount(models.Model):
    _inherit = "account.account"

    def _get_open_items_at_date(self, date, only_posted_moves):
        if not date or not self:
            return []
        move_states = ["posted"]
        if not only_posted_moves:
            move_states.append("draft")
        amls = self.env["account.move.line"].search(
            [
                ("reconciled", "=", False),
                ("account_id", "in", self.ids),
                "|",
                ("date_maturity", "<=", date),
                "&",
                ("date_maturity", "=", False),
                ("date", "<=", date),
                ("parent_state", "in", move_states),
            ]
        )
        return amls
