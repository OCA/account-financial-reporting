# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class MisReportInstance(models.Model):

    _inherit = 'mis.report.instance'

    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account', string='Analytic Account')

    @api.multi
    def preview(self):
        self.ensure_one()
        res = super(MisReportInstance, self).preview()
        res['context'] = {
            'account_analytic_id': self.account_analytic_id.id,
        }
        return res


class MisReportInstancePeriod(models.Model):
    _inherit = 'mis.report.instance.period'

    @api.multi
    def _get_additional_move_line_filter(self):
        self.ensure_one()
        res = super(MisReportInstancePeriod, self).\
            _get_additional_move_line_filter()
        val = self.env.context.get('account_analytic_id')
        if val:
            res.append(('analytic_account_id', '=', val))
        return res

    @api.multi
    def _get_additional_query_filter(self, query):
        self.ensure_one()
        res = super(MisReportInstancePeriod, self).\
            _get_additional_move_line_filter()
        # TODO filter on analytic account if query.model_id has
        #      a field of type account.analytic.account
        return res
