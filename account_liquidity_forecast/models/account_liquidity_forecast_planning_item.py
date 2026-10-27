# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountLiquidityForecastPlanningItem(models.Model):
    _name = "account.liquidity.forecast.planning.item"
    _description = "Liquidity Forecast Planning Item"

    name = fields.Char(required=True)
    group_id = fields.Many2one(
        string="Planning Group",
        comodel_name="account.liquidity.forecast.planning.group",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    company_currency_id = fields.Many2one(
        string="Company Currency",
        related="company_id.currency_id",
        readonly=True,
        store=True,
        precompute=True,
    )
    amount = fields.Monetary(currency_field="company_currency_id")
    direction = fields.Selection(
        selection=[("in", "Incoming"), ("out", "Outgoing")],
        default="in",
        index=True,
    )
    date = fields.Date(index=True)
    expiry_date = fields.Date(index=True)
