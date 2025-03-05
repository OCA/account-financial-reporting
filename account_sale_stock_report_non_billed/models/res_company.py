# Copyright 2022 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    stock_move_non_billed_threshold = fields.Date(
        string="Non Billed Threshold Date", default=fields.Date.context_today
    )
