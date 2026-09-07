# © 2026 Solvos Consultoría Informática (<http://www.solvos.es>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MisCashFlowPlan(models.Model):
    _name = "mis.cash.flow.plan"
    _description = "Cash Flow Plan"
    _order = "id desc"

    name = fields.Char(required=True)
    partner_id = fields.Many2one("res.partner", string="Partner")
    account_id = fields.Many2one("account.account", string="Account", required=True)
    balance = fields.Float(string="Balance / Amount", required=True)
    date_start = fields.Date(required=True, default=fields.Date.context_today)
    date_end = fields.Date(required=True)
    periodicity = fields.Selection(
        [("days", "Every X Days"), ("weeks", "Weekly"), ("months", "Monthly")],
        required=True,
        default="months",
    )
    every_x_days = fields.Integer(string="Interval (Days)", default=1)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    forecast_line_ids = fields.One2many(
        "mis.cash_flow.forecast_line",
        "cash_flow_plan_id",
        string="Generated Forecast Lines",
    )
    forecast_line_count = fields.Integer(
        compute="_compute_forecast_line_count",
        store=True,
    )

    @api.depends("forecast_line_ids")
    def _compute_forecast_line_count(self):
        counts = self.env["mis.cash_flow.forecast_line"]._read_group(
            domain=[("cash_flow_plan_id", "in", self.ids)],
            groupby=["cash_flow_plan_id"],
            aggregates=["__count"],
        )
        mapped = {r[0].id: r[1] for r in counts}
        for plan in self:
            plan.forecast_line_count = mapped.get(plan.id, 0)

    @api.constrains("date_start", "date_end", "every_x_days", "periodicity")
    def _check_constraints(self):
        for record in self:
            if record.date_end < record.date_start:
                raise ValidationError(
                    self.env._("End Date cannot be earlier than Start Date.")
                )
            if record.periodicity == "days" and record.every_x_days <= 0:
                raise ValidationError(
                    self.env._("The day interval must be greater than zero.")
                )

    def _prepare_plan_forecast_line(self, line_date):
        self.ensure_one()
        return {
            "name": self.name,
            "partner_id": self.partner_id.id,
            "account_id": self.account_id.id,
            "balance": self.balance,
            "date": line_date,
            "cash_flow_plan_id": self.id,
            "company_id": self.company_id.id,
        }

    def action_generate_forecast_lines(self):
        self.ensure_one()
        if self.forecast_line_ids:
            self.forecast_line_ids.unlink()
        forecast_obj = self.env["mis.cash_flow.forecast_line"]
        current_date = self.date_start
        lines_to_create = []
        limit_reached = False
        max_forecast_lines = self.company_id.cash_flow_plan_max_forecast_lines
        while current_date <= self.date_end:
            if len(lines_to_create) >= max_forecast_lines:
                limit_reached = True
                break
            lines_to_create.append(self._prepare_plan_forecast_line(current_date))
            if self.periodicity == "days":
                current_date += relativedelta(days=self.every_x_days)
            elif self.periodicity == "weeks":
                current_date += relativedelta(weeks=1)
            elif self.periodicity == "months":
                current_date += relativedelta(months=1)
        if lines_to_create:
            forecast_obj.create(lines_to_create)
        if limit_reached:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": self.env._("Generation limit reached"),
                    "message": self.env._(
                        "Only %(limit)d forecast lines were created. "
                        "Reduce the date range or increase the interval "
                        "to generate all lines.",
                        limit=max_forecast_lines,
                    ),
                    "type": "warning",
                    "sticky": True,
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }
        return False

    def action_view_generated_forecast_lines(self):
        self.ensure_one()
        return {
            "name": self.env._("Forecast Lines for Plan: %(name)s", name=self.name),
            "type": "ir.actions.act_window",
            "res_model": "mis.cash_flow.forecast_line",
            "view_mode": "list,form",
            "domain": [("cash_flow_plan_id", "=", self.id)],
            "context": {"default_cash_flow_plan_id": self.id},
            "target": "current",
        }
