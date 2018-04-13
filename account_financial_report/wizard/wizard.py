# -*- coding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
# Credits######################################################
#    Coded by:   Humberto Arocha humberto@openerp.com.ve
#                Angelica Barrios angelicaisabelb@gmail.com
#               Jordi Esteve <jesteve@zikzakmedia.com>
#               Javier Duran <javieredm@gmail.com>
#    Planified by: Humberto Arocha
#    Finance by: LUBCAN COL S.A.S http://www.lubcancol.com
#    Audited by: Humberto Arocha humberto@openerp.com.ve
#############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################
from openerp import _, fields, models
import time


class WizardReport(models.TransientModel):
    _name = "wizard.report"

    _columns = {
        'afr_id': fields.many2one(
            'afr', 'Custom Report',
            help='If you have already set a Custom Report, Select it Here.'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'currency_id': fields.many2one(
            'res.currency', 'Currency',
            help="Currency at which this report will be expressed. If not \
            selected will be used the one set in the company"),
        'inf_type': fields.selection([('BS', 'Balance Sheet'),
                                      ('IS', 'Income Statement')],
                                     'Type',
                                     required=True),
        'columns': fields.selection(
            [('one', 'End. Balance'),
             ('two', 'Debit | Credit'),
             ('four', 'Initial | Debit | Credit | YTD'),
             ('five', 'Initial | Debit | Credit | Period | YTD'),
             ('qtr', "4 QTR's | YTD"), ('thirteen', '12 Months | YTD')],
            'Columns', required=True),
        'display_account': fields.selection(
            [('all', 'All Accounts'),
             ('bal', 'With Balance'),
             ('mov', 'With movements'),
             ('bal_mov', 'With Balance / Movements')],
            'Display accounts'),
        'display_account_level': fields.integer(
            'Up to level',
            help='Display accounts up to this level (0 to show all)'),

        'account_list': fields.many2many('account.account',
                                         'rel_wizard_account',
                                         'account_list',
                                         'account_id',
                                         'Root accounts',
                                         required=True),

        'fiscalyear': fields.many2one('account.fiscalyear', 'Fiscal year',
                                      help='Fiscal Year for this report',
                                      required=True),
        'periods': fields.many2many(
            'account.period', 'rel_wizard_period',
            'wizard_id', 'period_id', 'Periods',
            help='All periods in the fiscal year if empty'),

        'analytic_ledger': fields.boolean(
            'Analytic Ledger',
            help="Allows to Generate an Analytic Ledger for accounts with \
            moves. Available when Balance Sheet and 'Initial | Debit | Credit \
            | YTD' are selected"),
        'journal_ledger': fields.boolean(
            'Journal Ledger',
            help="Allows to Generate an Journal Ledger for accounts with \
            moves. Available when Balance Sheet and 'Initial | Debit | Credit \
            | YTD' are selected"),
        'partner_balance': fields.boolean(
            'Partner Balance',
            help="Allows to Generate a Partner Balance for accounts with \
            moves. Available when Balance Sheet and 'Initial | Debit | Credit \
            | YTD' are selected"),
        'tot_check': fields.boolean('Summarize?',
                                    help='Checking will add a new line at the \
                                    end of the Report which will Summarize \
                                    Columns in Report'),
        'lab_str': fields.char('Description',
                               help='Description for the Summary', size=128),

        'target_move': fields.selection(
            [('posted', 'All Posted Entries'),
             ('all', 'All Entries'),
             ], 'Entries to Include',
            required=True,
            help='Print All Accounting Entries or just Posted Accounting \
            Entries'),
        # ~ Deprecated fields
        'filter': fields.selection([('bydate', 'By Date'),
                                    ('byperiod', 'By Period'),
                                    ('all', 'By Date and Period'),
                                    ('none', 'No Filter')],
                                   'Date/Period Filter'),
        'date_to': fields.date('End date'),
        'date_from': fields.date('Start date'),
    }

    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-%m-%d'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
        'filter': lambda *a: 'byperiod',
        'display_account_level': lambda *a: 0,
        'inf_type': lambda *a: 'BS',
        'company_id': lambda self, cr, uid, c: self.pool['res.company'].
        _company_default_get(cr, uid, 'account.invoice', context=c),
        'fiscalyear': lambda self, cr, uid, c: self.
        pool['account.fiscalyear'].find(cr, uid),
        'display_account': lambda *a: 'bal_mov',
        'columns': lambda *a: 'five',
        'target_move': 'posted',
    }

    def onchange_inf_type(self, cr, uid, ids, inf_type, context=None):
        if context is None:
            context = {}
        res = {'value': {}}

        if inf_type != 'BS':
            res['value'].update({'analytic_ledger': False})

        return res

    def onchange_columns(self, cr, uid, ids, columns, fiscalyear, periods,
                         context=None):
        if context is None:
            context = {}
        res = {'value': {}}

        p_obj = self.pool.get("account.period")
        all_periods = p_obj.search(cr, uid,
                                   [('fiscalyear_id', '=', fiscalyear),
                                    ('special', '=', False)], context=context)
        s = set(periods[0][2])
        t = set(all_periods)
        go = periods[0][2] and s.issubset(t) or False

        if columns != 'four':
            res['value'].update({'analytic_ledger': False})

        if columns in ('qtr', 'thirteen'):
            res['value'].update({'periods': all_periods})
        else:
            if go:
                res['value'].update({'periods': periods})
            else:
                res['value'].update({'periods': []})
        return res

    def onchange_analytic_ledger(self, cr, uid, ids, company_id,
                                 analytic_ledger, context=None):
        if context is None:
            context = {}
        context['company_id'] = company_id
        res = {'value': {}}
        cur_id = self.pool.get('res.company').browse(
            cr, uid, company_id, context=context).currency_id.id
        res['value'].update({'currency_id': cur_id})
        return res

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        if context is None:
            context = {}
        context['company_id'] = company_id
        res = {'value': {}}

        if not company_id:
            return res

        cur_id = self.pool.get('res.company').browse(
            cr, uid, company_id, context=context).currency_id.id
        fy_id = self.pool.get('account.fiscalyear').find(
            cr, uid, context=context)
        res['value'].update({'fiscalyear': fy_id})
        res['value'].update({'currency_id': cur_id})
        res['value'].update({'account_list': []})
        res['value'].update({'periods': []})
        res['value'].update({'afr_id': None})
        return res

    def onchange_afr_id(self, cr, uid, ids, afr_id, context=None):
        if context is None:
            context = {}
        res = {'value': {}}
        if not afr_id:
            return res
        afr_brw = self.pool.get('afr').browse(cr, uid, afr_id, context=context)
        res['value'].update({
            'currency_id': afr_brw.currency_id and afr_brw.currency_id.id or
            afr_brw.company_id.currency_id.id,
        })
        res['value'].update({'inf_type': afr_brw.inf_type or 'BS'})
        res['value'].update({'columns': afr_brw.columns or 'five'})
        res['value'].update({
            'display_account': afr_brw.display_account or 'bal_mov',
        })
        res['value'].update({
            'display_account_level': afr_brw.display_account_level or 0
        })
        res['value'].update({
            'fiscalyear': afr_brw.fiscalyear_id and afr_brw.fiscalyear_id.id
        })
        res['value'].update({'account_list': [
                            acc.id for acc in afr_brw.account_ids]})
        res['value'].update({'periods': [p.id for p in afr_brw.period_ids]})
        res['value'].update({
                            'analytic_ledger':
                            afr_brw.analytic_ledger or False})
        res['value'].update({'tot_check': afr_brw.tot_check or False})
        res['value'].update({'lab_str': afr_brw.lab_str or _(
            'Write a Description for your Summary Total')})
        return res

    def _get_defaults(self, cr, uid, data, context=None):
        if context is None:
            context = {}
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        if user.company_id:
            company_id = user.company_id.id
        else:
            company_id = self.pool['res.company'].search(
                cr, uid, [('parent_id', '=', False)])[0]
        data['form']['company_id'] = company_id
        fiscalyear_obj = self.pool['account.fiscalyear']
        data['form']['fiscalyear'] = fiscalyear_obj.find(cr, uid)
        data['form']['context'] = context
        return data['form']

    def _check_state(self, cr, uid, data, context=None):
        if context is None:
            context = {}
        if data['form']['filter'] == 'bydate':
            self._check_date(cr, uid, data, context)
        return data['form']

    def _check_date(self, cr, uid, data, context=None):
        if context is None:
            context = {}

        if data['form']['date_from'] > data['form']['date_to']:
            raise osv.except_osv(_('Error !'), (
                'La fecha final debe ser mayor a la inicial'))

        sql = """SELECT f.id, f.date_start, f.date_stop
            FROM account_fiscalyear f
            WHERE '%s' = f.id """ % (data['form']['fiscalyear'])
        cr.execute(sql)
        res = cr.dictfetchall()

        if res:
            if data['form']['date_to'] > res[0]['date_stop'] or\
                   data['form']['date_from'] < res[0]['date_start']:
                raise osv.except_osv(_('UserError'),
                                     'Las fechas deben estar entre %s y %s'
                                     % (res[0]['date_start'],
                                        res[0]['date_stop']))
            else:
                return 'report'
        else:
            raise osv.except_osv(_('UserError'), 'No existe periodo fiscal')

    def period_span(self, cr, uid, ids, fy_id, context=None):
        if context is None:
            context = {}
        ap_obj = self.pool.get('account.period')
        fy_id = fy_id and type(fy_id) in (list, tuple) and fy_id[0] or fy_id
        if not ids:
            # ~ No hay periodos
            return ap_obj.search(cr, uid, [('fiscalyear_id', '=', fy_id),
                                           ('special', '=', False)],
                                 order='date_start asc')

        ap_brws = ap_obj.browse(cr, uid, ids, context=context)
        date_start = min([period.date_start for period in ap_brws])
        date_stop = max([period.date_stop for period in ap_brws])

        return ap_obj.search(cr, uid, [('fiscalyear_id', '=', fy_id),
                                       ('special', '=', False),
                                       ('date_start', '>=', date_start),
                                       ('date_stop', '<=', date_stop)],
                             order='date_start asc')

    def print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}

        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids[0])

        if data['form']['filter'] == 'byperiod':
            del data['form']['date_from']
            del data['form']['date_to']

            data['form']['periods'] = self.period_span(
                cr, uid,
                data['form']['periods'],
                data['form']['fiscalyear'])

        elif data['form']['filter'] == 'bydate':
            self._check_date(cr, uid, data)
            del data['form']['periods']
        elif data['form']['filter'] == 'none':
            del data['form']['date_from']
            del data['form']['date_to']
            del data['form']['periods']
        else:
            self._check_date(cr, uid, data)
            lis2 = str(data['form']['periods']).replace(
                "[", "(").replace("]", ")")
            sqlmm = """select min(p.date_start) as inicio,
                              max(p.date_stop) as fin
                       from account_period p
                       where p.id in %s""" % lis2
            cr.execute(sqlmm)
            minmax = cr.dictfetchall()
            if minmax:
                if (data['form']['date_to'] < minmax[0]['inicio']) \
                        or (data['form']['date_from'] > minmax[0]['fin']):
                    raise osv.except_osv(_('Error !'), _(
                        'La interseccion entre el periodo y fecha es vacio'))

        if data['form']['columns'] == 'one':
            name = 'afr.1cols'
        if data['form']['columns'] == 'two':
            name = 'afr.2cols'
        if data['form']['columns'] == 'four':
            if data['form']['analytic_ledger'] \
                    and data['form']['inf_type'] == 'BS':
                name = 'afr.analytic.ledger'
            elif data['form']['journal_ledger'] \
                    and data['form']['inf_type'] == 'BS':
                name = 'afr.journal.ledger'
            elif data['form']['partner_balance'] \
                    and data['form']['inf_type'] == 'BS':
                name = 'afr.partner.balance'
            else:
                name = 'afr.4cols'
        if data['form']['columns'] == 'five':
            name = 'afr.5cols'
        if data['form']['columns'] == 'qtr':
            name = 'afr.qtrcols'
        if data['form']['columns'] == 'thirteen':
            name = 'afr.13cols'

        return {'type': 'ir.actions.report.xml',
                'report_name': name,
                'datas': data}
