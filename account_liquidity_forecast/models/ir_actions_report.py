# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    @api.model
    def _prepare_liquidity_forecast_report_context(self, data):
        lang = data and data.get("liquidity_forecast_report_lang") or ""
        return dict(self.env.context or {}, lang=lang) if lang else False

    @api.model
    def _render_qweb_html(self, report_ref, docids, data=None):
        context = self._prepare_liquidity_forecast_report_context(data)
        obj = self.with_context(**context) if context else self
        return super(IrActionsReport, obj)._render_qweb_html(
            report_ref, docids, data=data
        )

    @api.model
    def _render_xlsx(self, report_ref, docids, data=None):
        context = self._prepare_liquidity_forecast_report_context(data)
        obj = self.with_context(**context) if context else self
        return super(IrActionsReport, obj)._render_xlsx(report_ref, docids, data=data)
