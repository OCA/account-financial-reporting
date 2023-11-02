# Copyright 2023 Ernesto García
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountAgeReportConfiguration(models.Model):
    _name = "account.age.report.configuration"
    _description = "Model to set intervals for Age partner balance report"

    name = fields.Char()
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    line_ids = fields.One2many(
        "account.age.report.configuration.line", "account_age_report_config_id"
    )


class AccountAgeReportConfigurationLine(models.Model):
    _name = "account.age.report.configuration.line"

    name = fields.Char()
    code = fields.Char()
    account_age_report_config_id = fields.Many2one("account.age.report.configuration")
    lower_limit = fields.Integer()
    superior_limit = fields.Integer()
