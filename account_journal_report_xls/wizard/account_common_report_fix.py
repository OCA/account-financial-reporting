# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""
Bypass of bug in Odoo:
The financial reports do not work on first and last day of the Fiscal Year.
This fix can be removed after merge of
PR https://github.com/odoo/odoo/pull/14891.
"""
import logging
import time
from openerp import api, fields, models
_logger = logging.getLogger(__name__)


class AccountCommonReportFix(object):

    @api.model
    def _default_fiscalyear_id(self):
        _logger.debug(
            '%s, fix cf. PR https://github.com/odoo/odoo/pull/14891',
            self._name)
        fy_id = super(AccountCommonReportFix, self)._get_fiscalyear()
        if fy_id:
            return self.env['account.fiscalyear'].browse(fy_id)

        now = time.strftime('%Y-%m-%d')
        ids = self._context.get('active_ids', [])
        if ids and self._context.get('active_model') == 'account.account':
            company = self.env['account.account'].browse(ids[0])
        else:  # use current company id
            company = self.env.user.company_id
        domain = [('company_id', '=', company.id),
                  ('date_start', '<=', now), ('date_stop', '>=', now)]
        return self.env['account.fiscalyear'].search(domain, limit=1)

    def onchange_chart_id(self, cr, uid, ids,
                          chart_account_id=False, context=None):
        _logger.debug(
            '%s, fix cf. PR https://github.com/odoo/odoo/pull/14891',
            self._name)
        res = super(AccountCommonReportFix, self).onchange_chart_id(
            cr, uid, ids, chart_account_id=chart_account_id, context=context)
        if not res.get('fiscalyear_id'):
            if chart_account_id:
                company_id = self.pool['account.account'].browse(
                    cr, uid, chart_account_id, context=context).company_id.id
                now = time.strftime('%Y-%m-%d')
                domain = [('company_id', '=', company_id),
                          ('date_start', '<=', now), ('date_stop', '>=', now)]
                fiscalyears = self.pool['account.fiscalyear'].search(
                    cr, uid, domain, limit=1)
                res['value'] = {
                    'company_id': company_id,
                    'fiscalyear_id': fiscalyears and fiscalyears[0] or False,
                    }
        return res


class AccountPrintJournalXls(AccountCommonReportFix,
                             models.TransientModel):
    _inherit = 'account.print.journal.xls'

    fiscalyear_id = fields.Many2one(
        default=lambda self: self._default_fiscalyear_id())
