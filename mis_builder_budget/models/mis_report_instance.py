# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.osv import expression

from odoo.addons.mis_builder.models.accounting_none import AccountingNone
from odoo.addons.mis_builder.models.mis_safe_eval import mis_safe_eval


class MisReportInstance(models.Model):

    _inherit = 'mis.report.instance'

    def _add_column_mis_budget(
            self, aep, kpi_matrix, period, label, description):

        # fetch budget data for the period
        base_domain = expression.AND([
            [('budget_id', '=', period.source_mis_budget.id)],
            period._get_additional_budget_item_filter(),
        ])
        kpi_data = self.env['mis.budget.item']._query_kpi_data(
            period.date_from, period.date_to, base_domain)

        locals_dict = {}
        locals_dict.update(self.report_id.prepare_locals_dict())

        def eval_expressions(expressions, locals_dict):
            vals = []
            drilldown_args = []
            name_error = False
            for expr in expressions:
                val = AccountingNone
                drilldown_arg = None
                if expr:
                    if expr.kpi_id.budgetable:
                        val = kpi_data.get(expr, AccountingNone)
                        # TODO drilldown
                    elif expr.name:
                        val = mis_safe_eval(expr.name, locals_dict)
                vals.append(val)
                drilldown_args.append(drilldown_arg)
            return vals, drilldown_args, name_error

        self.report_id._declare_and_compute_col(
            kpi_matrix, period.id, label, description, period.subkpi_ids,
            locals_dict, eval_expressions, None)

    def _add_column(self, aep, kpi_matrix, period, label, description):
        if period.source == 'mis_budget':
            return self._add_column_mis_budget(
                aep, kpi_matrix, period, label, description)
        else:
            return super(MisReportInstance, self)._add_column(
                aep, kpi_matrix, period, label, description)
