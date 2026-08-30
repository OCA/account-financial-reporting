# Copyright 2022 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    stock_move_non_billed_threshold = fields.Date(
        related="company_id.stock_move_non_billed_threshold", readonly=False
    )
    default_interval_restrict_invoices = fields.Boolean(
        string="Restrict invoices using the date interval",
        default_model="account.sale.stock.report.non.billed.wiz",
    )
