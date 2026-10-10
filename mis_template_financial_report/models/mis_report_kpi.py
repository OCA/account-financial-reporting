# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class MisReportKpi(models.Model):
    _inherit = "mis.report.kpi"

    split_after = fields.Boolean(
        help="Split the table after this KPI. This allows displaying KPIs next to each "
        "other in non-comparison mode",
    )
