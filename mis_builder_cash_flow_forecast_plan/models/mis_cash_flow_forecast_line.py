# © 2026 Solvos Consultoría Informática (<http://www.solvos.es>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models


class MisCashFlowForecastLine(models.Model):
    _inherit = "mis.cash_flow.forecast_line"

    category_id = fields.Many2one(
        "mis.cash.flow.forecast.category",
        string="Category",
        ondelete="set null",
        index=True,
    )

    cash_flow_plan_id = fields.Many2one(
        "mis.cash.flow.plan",
        string="Origin Cash Flow Plan",
        ondelete="cascade",
        index=True,
    )
