# -*- encoding: utf-8 -*-
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

from openerp.osv import osv, fields
import time
from openerp.tools.translate import _


class account_financial_report(osv.osv):
    _name = "afr"

    _columns = {
        'name': fields.char('Name', size=128, required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'currency_id': fields.many2one('res.currency', 'Currency',
                                       help="Currency at which this report \
                                       will be expressed. If not selected \
                                       will be used the one set in the \
                                       company"),
        'inf_type': fields.selection([('BS', 'Balance Sheet'),
                                      ('IS', 'Income Statement')],
                                     'Type',
                                     required=True),
        'columns': fields.selection(
            [('one', 'End. Balance'),
             ('two', 'Debit | Credit'),
             ('four', 'Initial | Debit | Credit | YTD'),
             ('five', 'Initial | Debit | Credit | Period | YTD'),
             ('qtr', "4 QTR's | YTD"),
             ('thirteen', '12 Months | YTD')], 'Columns', required=True),
        'display_account': fields.selection(
            [('all', 'All Accounts'),
             ('bal', 'With Balance'),
             ('mov', 'With movements'),
             ('bal_mov', 'With Balance / Movements')], 'Display accounts'),
        'display_account_level': fields.integer('Up to level',
                                                help='Display accounts up to \
                                                this level (0 to show all)'),
        'account_ids': fields.many2many('account.account', 'afr_account_rel',
                                        'afr_id', 'account_id',
                                        'Root accounts', required=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal year',
                                         help='Fiscal Year for this report',
                                         required=True),
        'period_ids': fields.many2many(
            'account.period', 'afr_period_rel', 'afr_id', 'period_id',
            'Periods', help='All periods in the fiscal year if empty'),

        'analytic_ledger': fields.boolean(
            'Analytic Ledger',
            help="Allows to Generate an Analytic Ledger for accounts with \
            moves. Available when Balance Sheet and 'Initial | Debit \
            | Credit | YTD' are selected"),
        'journal_ledger': fields.boolean(
            'journal Ledger',
            help="Allows to Generate an journal Ledger for accounts with \
            moves. Available when Balance Sheet and 'Initial | Debit | \
            Credit | YTD' are selected"),
        'partner_balance': fields.boolean(
            'Partner Balance',
            help="Allows to Generate a Partner Balance for accounts with \
            moves. Available when  Balance Sheet and 'Initial | Debit | \
            Credit | YTD' are selected"),
        'tot_check': fields.boolean(
            'Summarize?',
            help='Checking will add a new line at the end of the Report which \
                  will Summarize Columns in Report'),
        'lab_str': fields.char('Description',
                               help='Description for the Summary',
                               size=128),
        'target_move': fields.selection(
            [('posted', 'All Posted Entries'),
             ('all', 'All Entries'), ],
            'Entries to Include', required=True,
            help='Print All Accounting Entries or just Posted \
                  Accounting Entries'),

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
        'display_account_level': lambda *a: 0,
        'inf_type': lambda *a: 'BS',
        'company_id': lambda self, cr, uid, c:
        self.pool.get(
            'res.company')._company_default_get(
            cr,
            uid,
            'account.invoice',
            context=c),
        'fiscalyear_id': lambda self, cr, uid, c:
        self.pool.get('account.fiscalyear').find(cr, uid),
        'display_account': lambda *a: 'bal_mov',
        'columns': lambda *a: 'five',

        'date_from': lambda *a: time.strftime('%Y-%m-%d'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
        'filter': lambda *a: 'byperiod',
        'target_move': 'posted',
    }

    def copy(self, cr, uid, id, defaults, context=None):
        if context is None:
            context = {}
        previous_name = self.browse(cr, uid, id, context=context).name
        new_name = _('Copy of %s') % previous_name
        lst = self.search(cr, uid, [(
            'name', 'like', new_name)], context=context)
        if lst:
            new_name = '%s (%s)' % (new_name, len(lst) + 1)
        defaults['name'] = new_name
        return (
            super(
                account_financial_report,
                self).copy(
                cr,
                uid,
                id,
                defaults,
                context=context)
        )

    def onchange_inf_type(self, cr, uid, ids, inf_type, context=None):
        if context is None:
            context = {}
        res = {'value': {}}

        if inf_type != 'BS':
            res['value'].update({'analytic_ledger': False})

        return res

    def onchange_columns(self, cr, uid, ids, columns,
                         fiscalyear_id, period_ids, context=None):
        if context is None:
            context = {}
        res = {'value': {}}

        if columns != 'four':
            res['value'].update({'analytic_ledger': False})

        if columns in ('qtr', 'thirteen'):
            p_obj = self.pool.get("account.period")
            period_ids = p_obj.search(cr, uid,
                                      [('fiscalyear_id', '=', fiscalyear_id),
                                       ('special', '=', False)],
                                      context=context)
            res['value'].update({'period_ids': period_ids})
        else:
            res['value'].update({'period_ids': []})
        return res

    def onchange_analytic_ledger(
            self, cr, uid, ids, company_id, analytic_ledger, context=None):
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
        res['value'].update({'fiscalyear_id': fy_id})
        res['value'].update({'currency_id': cur_id})
        res['value'].update({'account_ids': []})
        res['value'].update({'period_ids': []})
        return res


account_financial_report()
