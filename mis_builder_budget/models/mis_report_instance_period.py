# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)


class MisReportInstancePeriod(models.Model):

    _inherit = 'mis.report.instance.period'

    source = fields.Selection(
        [('actuals', 'Actuals'),
         ('mis_budget', 'MIS Budget')],
        default='actuals',
        required=True,
        help="Actuals: current data, from accounting and other queries.\n"
             "MIS Budget: MIS Budget data."
    )

    def _compute_mis_budget(self, lang_id, aep):
        mis_report = self.report_instance_id.report_id
        budget = self.env['mis.budget'].search(
            [('report_id', '=', mis_report.id)])

        res = {}
        for kpi in mis_report.kpi_ids:

            budget_items = budget.item_ids.filtered(
                lambda r: r.kpi_id == kpi)
            budget_item = budget_items.filtered(
                lambda r: r.date_from == self.date_from and
                r.date_to == self.date_to)
            if len(budget_item) != 1:
                raise UserError(_(
                    "Configuration Error !\n"
                    "Budget Item (id: %s) Period/Dates do not "
                    "correspond with report period %s")
                    % (budget_item.id, self.name))

            kpi_val = budget_item.amount
            kpi_val_rendered = kpi.render(lang_id, kpi_val)
            kpi_val_comment = kpi.name + ' - ' + _("budget")

            res[kpi.name] = {
                'val': kpi_val,
                'val_r': kpi_val_rendered,
                'val_c': kpi_val_comment,
                'style': None,
                'prefix': False,
                'suffix': False,
                'dp': kpi.dp,
                'is_percentage': kpi.type == 'pct',
                'period_id': self.id,
                'expr': False,
                'drilldown': False,
            }
        return res

    @api.multi
    def _compute(self, lang_id, aep):
        self.ensure_one()
        if self.source == 'mis_budget':
            res = self._compute_mis_budget(lang_id, aep)
        else:
            res = super(MisReportInstancePeriod, self)._compute(lang_id, aep)
        return res
