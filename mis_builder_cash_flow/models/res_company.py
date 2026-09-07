# © 2026 Solvos Consultoría Informática (<http://www.solvos.es>)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    cash_flow_plan_max_forecast_lines = fields.Integer(
        default=100,
        help="Maximum number of forecast lines a Cash Flow Plan can generate "
        "at once when using 'Generate Forecast Lines'.",
    )
