# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class MisReportInstancePeriod(models.Model):
    _inherit = "mis.report.instance.period"

    def _get_additional_move_line_filter(self):
        """Add the posted condition ."""
        domain = super()._get_additional_move_line_filter()
        if (
            self._get_aml_model_name() == "mis.cash_flow"
            and self.report_instance_id.target_move == "posted"
        ):
            domain += [("state", "=", "posted")]
        return domain
