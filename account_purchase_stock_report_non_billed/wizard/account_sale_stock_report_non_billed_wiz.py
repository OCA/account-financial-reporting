# Copyright 2022 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models
from odoo.osv import expression


class AccountSaleStockReportNonBilledWiz(models.TransientModel):
    _inherit = "account.sale.stock.report.non.billed.wiz"

    def _get_search_domain(self):
        domain = super()._get_search_domain()
        res_domain = expression.OR(
            [
                domain,
                [
                    ("date_done", ">=", self.stock_move_non_billed_threshold),
                    ("date_done", "<=", self.date_check),
                    ("purchase_line_id", "!=", False),
                    ("state", "=", "done"),
                    ("scrapped", "=", False),
                    "|",
                    ("location_id.usage", "=", "supplier"),
                    "&",
                    ("location_dest_id.usage", "=", "supplier"),
                    ("to_refund", "=", True),
                ],
            ]
        )
        return res_domain

    @api.model
    def discart_kits_from_moves(self, stock_moves):
        res = super().discart_kits_from_moves(stock_moves)
        return res + stock_moves.filtered(
            lambda move: move.product_id == move.purchase_line_id.product_id
        )
