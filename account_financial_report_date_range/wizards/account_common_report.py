# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountCommonReport(models.TransientModel):
    _inherit = 'account.common.report'

    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date range',
    )

    @api.onchange('date_range_id')
    def _onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end
