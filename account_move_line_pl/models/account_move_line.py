from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends('balance')
    def _compute_balance_pl(self):
        for line in self:
            line.balance_pl = -line.balance

    balance_pl = fields.Monetary(
        string='Profit/Loss',
        compute='_compute_balance_pl',
        store=True,
        precompute=True,
        currency_field='company_currency_id',
    )
    account_type = fields.Selection(string="Account Type", store=True)
