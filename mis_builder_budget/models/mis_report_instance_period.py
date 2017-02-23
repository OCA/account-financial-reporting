# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


SRC_MIS_BUDGET = 'mis_budget'


class MisReportInstancePeriod(models.Model):

    _inherit = 'mis.report.instance.period'

    source = fields.Selection(
        selection_add=[
            (SRC_MIS_BUDGET, 'MIS Budget'),
        ],
    )
    source_mis_budget = fields.Many2one(
        comodel_name='mis.budget',
        string='Budget',
    )

    @api.multi
    def _get_additional_budget_item_filter(self):
        """ Prepare a filter to apply on all budget items

        This filter is applied with a AND operator on all
        budget items. This hook is intended
        to be inherited, and is useful to implement filtering
        on analytic dimensions or operational units.

        Returns an Odoo domain expression (a python list)
        compatible with mis.budget.item."""
        self.ensure_one()
        return []
