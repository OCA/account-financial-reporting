# Copyright 2023 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class LiquidityForecastReportWizard(models.TransientModel):

    _name = "account.liquidity.forecast.report.wizard"
    _description = "Liquidity Forecast Report Wizard"

    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
        required=False,
        string="Company",
    )
    period_length = fields.Selection(
        selection=[
            ("days", "Days"),
            ("weeks", "Weeks"),
            ("months", "Months"),
        ],
        default="days",
        required=True,
    )
    date_to = fields.Date(required=True, default=fields.Date.today)
    target_move = fields.Selection(
        [("posted", "All Posted Entries"), ("all", "All Entries")],
        string="Target Moves",
        required=True,
        default="posted",
    )

    def button_export_html(self):
        self.ensure_one()
        report_type = "qweb-html"
        return self._export(report_type)

    def button_export_pdf(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def button_export_xlsx(self):
        self.ensure_one()
        report_type = "xlsx"
        return self._export(report_type)

    def _export(self, report_type):
        """Default export is PDF."""
        return self._print_report(report_type)

    def _print_report(self, report_type):
        self.ensure_one()
        data = self._prepare_report_liquidity_forecast()
        if report_type == "xlsx":
            report_name = "report_liquidity_forecast_xlsx"
        else:
            report_name = "account_liquidity_forecast.liquidity_forecast"
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
            .report_action(self, data=data)
        )

    def _prepare_report_liquidity_forecast(self):
        self.ensure_one()
        return {
            "wizard_id": self.id,
            "date_from": fields.Date.today(),
            "date_to": self.date_to,
            "only_posted_moves": self.target_move == "posted",
            "company_id": self.company_id.id,
            "res_company": self.company_id,
            "period_length": self.period_length,
            "liquidity_forecast_report_lang": self.env.lang,
        }
