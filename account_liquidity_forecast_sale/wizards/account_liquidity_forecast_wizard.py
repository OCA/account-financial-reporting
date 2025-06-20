# Copyright 2025 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class LiquidityForecastReportWizard(models.TransientModel):

    _inherit = "account.liquidity.forecast.report.wizard"

    include_so_draft = fields.Boolean(default=True, string="Include Draft SO")

    def _prepare_report_liquidity_forecast(self):
        self.ensure_one()
        res = super()._prepare_report_liquidity_forecast()
        res.update({"include_so_draft": self.include_so_draft})
        return res
