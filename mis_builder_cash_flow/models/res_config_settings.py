# © 2026 Solvos Consultoría Informática (<http://www.solvos.es>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cash_flow_plan_max_forecast_lines = fields.Integer(
        related="company_id.cash_flow_plan_max_forecast_lines",
        string="Cash Flow Plan Max Forecast Lines",
        readonly=False,
    )
