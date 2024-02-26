from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends("balance", "account_internal_group")
    def _compute_balance_pl(self):
        for line in self:
            if line.account_internal_group in ("income", "expense"):
                line.balance_pl = -line.balance
            else:
                line.balance_pl = 0

    balance_pl = fields.Monetary(
        string="Profit/Loss",
        compute="_compute_balance_pl",
        store=True,
        precompute=True,
        currency_field="company_currency_id",
    )
    account_type = fields.Selection(store=True)
