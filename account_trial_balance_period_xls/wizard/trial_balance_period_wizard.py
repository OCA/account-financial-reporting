# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.tools.translate import _
from openerp.osv import orm, fields
import time
import logging
_logger = logging.getLogger(__name__)


class account_trial_balance_period_wizard(orm.TransientModel):
    _name = 'trial.balance.period.wizard'
    _description = 'Trial Balance per Period'

    _columns = {
        'chart_account_id': fields.many2one(
            'account.account', 'Chart of Account', required=True,
            domain=[('parent_id', '=', False)],
            help='Select Charts of Accounts'),
        'company_id': fields.related(
            'chart_account_id', 'company_id', type='many2one',
            relation='res.company', string='Company', readonly=True),
        'fiscalyear_id': fields.many2one(
            'account.fiscalyear', 'Fiscal Year', required=True),
        'period_from': fields.many2one(
            'account.period', 'Start Period', required=True),
        'period_to': fields.many2one(
            'account.period', 'End Period', required=True),
        'target_move': fields.selection([
            ('posted', 'All Posted Entries'),
            ('all', 'All Entries'),
            ], 'Target Moves', required=True),
        'level': fields.integer(
            'Level',
            help="Specify the account level to include in the report.\n"
                 "Specify '0' to show details of all selected accounts "
                 "as well as it's child accounts."),
        'journal_ids': fields.many2many(
            'account.journal', string='Journals',
            help="Only entries from selected journals will be printed."),
        'account_ids': fields.many2many(
            'account.account', string='Filter on accounts',
            help="Only selected accounts will be printed."),
        }

    def _get_account(self, cr, uid, context=None):
        accounts = self.pool.get('account.account').search(
            cr, uid, [('parent_id', '=', False)], limit=1)
        return accounts and accounts[0] or False

    def _get_all_journals(self, cr, uid, context=None):
        return self.pool.get('account.journal').search(cr, uid, [])

    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(
            cr, uid, [('date_start', '<', now), ('date_stop', '>', now)],
            limit=1)
        return fiscalyears and fiscalyears[0] or False

    def _get_company(self, cr, uid, context=None):
        return self.pool.get('res.company')._company_default_get(
            cr, uid, 'account.common.report', context=context)

    _defaults = {
        'fiscalyear_id': _get_fiscalyear,
        'company_id': _get_company,
        'chart_account_id': _get_account,
        'target_move': 'posted',
    }

    def onchange_chart_id(self, cr, uid, ids,
                          chart_account_id=False, context=None):
        if chart_account_id:
            company_id = self.pool.get('account.account').browse(
                cr, uid, chart_account_id, context=context).company_id.id
        return {'value': {'company_id': company_id}}

    def fy_period_ids(self, cr, uid, fiscalyear_id):
        """ returns all periods from a fiscalyear sorted by date """
        fy_period_ids = []
        cr.execute(
            "SELECT id FROM account_period "
            "WHERE fiscalyear_id=%s AND NOT special "
            "ORDER BY date_start",
            (fiscalyear_id,))
        res = cr.fetchall()
        if res:
            fy_period_ids = map(lambda x: x[0], res)
        return fy_period_ids

    def onchange_fiscalyear_id(self, cr, uid, ids,
                               fiscalyear_id=False, context=None):
        res = {'value': {}}
        fy_period_ids = self.fy_period_ids(cr, uid, fiscalyear_id)
        if fy_period_ids:
            res['value']['period_from'] = fy_period_ids[0]
            res['value']['period_to'] = fy_period_ids[-1]
        return res

    def xls_export(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        wiz_form = self.browse(cr, uid, ids)[0]
        fiscalyear_id = wiz_form.fiscalyear_id.id
        company_id = wiz_form.company_id.id
        period_from = wiz_form.period_from
        period_to = wiz_form.period_to
        if period_from.date_start > period_to.date_start:
            raise orm.except_orm(
                _('Error'),
                _('The Start Period must precede the End Period !'))
        cr.execute(
            "SELECT id FROM account_period "
            "WHERE date_start>=%s AND date_stop<=%s "
            "AND company_id=%s AND NOT special "
            "ORDER BY date_start",
            (period_from.date_start, period_to.date_stop, company_id))
        period_ids = map(lambda x: x[0], cr.fetchall())
        if period_from.special:
            period_ids.insert(0, period_from.id)
        if period_to.special:
            period_ids.append(period_to.id)
        if wiz_form.journal_ids:
            journal_ids = [j.id for j in wiz_form.journal_ids]
        else:
            journal_ids = self._get_all_journals(cr, uid)
        if wiz_form.target_move == 'posted':
            move_states = ['posted']
        else:
            move_states = ['draft', 'posted']
        if wiz_form.account_ids:
            accounts = []
            for account in wiz_form.account_ids:
                if account.parent_id in accounts:
                    continue
                else:
                    accounts.append(account)
            account_ids = [a.id for a in accounts]
        else:
            account_ids = [wiz_form.chart_account_id.id]

        datas = {
            'model': 'account.account',
            'ids': account_ids,
            'journal_ids': journal_ids,
            'company_id': company_id,
            'period_ids': period_ids,
            'fiscalyear_id': fiscalyear_id,
            'move_states': move_states,
            'level': wiz_form.level,
            'account_ids': account_ids,
        }

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.trial.balance.period.xls',
            'datas': datas}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
