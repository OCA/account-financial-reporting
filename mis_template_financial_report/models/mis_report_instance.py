# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import copy
from collections import OrderedDict

from odoo import api, fields, models


class MisReportInstance(models.Model):
    _inherit = "mis.report.instance"

    allow_horizontal = fields.Boolean(compute="_compute_allow_horizontal")
    horizontal = fields.Boolean()

    @api.depends("report_id")
    def _compute_allow_horizontal(self):
        """Indicate that the instance supports horizontal rendering."""
        for instance in self:
            instance.allow_horizontal = any(
                instance.mapped("report_id.kpi_ids.split_after")
            )

    def compute(self):
        if not self.horizontal:
            return super().compute()

        full_matrix = self._compute_matrix()

        matrices = self._split_matrix(full_matrix)

        result = full_matrix.as_dict()
        result["split_matrices"] = [extra_matrix.as_dict() for extra_matrix in matrices]

        return result

    def _split_matrix(self, original_matrix):
        """Split a matrix according to the split_after flag in the kpis used"""
        result = []

        def clone_matrix():
            clone = copy.copy(original_matrix)
            clone._kpi_rows = OrderedDict()
            result.append(clone)
            return clone

        current = clone_matrix()

        for kpi in original_matrix._kpi_rows:
            current._kpi_rows[kpi] = original_matrix._kpi_rows[kpi]
            if kpi.split_after:
                current = clone_matrix()

        return result
