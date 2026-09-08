# Copyright 2025 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountFinancialReportColumn(models.Model):
    _name = "account.financial.report.column"
    _description = "Manage column options in financial reports"
    _order = "sequence, id"

    res_model = fields.Char()
    sequence = fields.Integer()
    name = fields.Char(required=True, translate=True)
    expression_label = fields.Char(required=True)
    is_visible = fields.Boolean(string="Show", default=True)
    field_type = fields.Char()
    limit = fields.Integer()
