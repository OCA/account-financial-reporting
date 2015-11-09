# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import orm, fields


class AccountAgedTrialBalance(orm.TransientModel):
    """Will launch age partner balance report.
    This report is based on Open Invoice Report
    and share a lot of knowledge with him
    """

    _inherit = "open.invoices.webkit"
    _name = "account.aged.trial.balance.webkit"
    _description = "Aged partner balanced"

    _columns = {
        'detailed_by_invoice': fields.boolean(
            "Detailed by Invoice",
            help="Provide an aged partner balance report with invoice "
                 "details"
        ),
        'aging_method': fields.selection(
            [('due_date', 'Due Date'),
             ('invoice_date', 'Invoice Date')],
            'Aged from',
            required=True
        ),
    }

    _defaults = {
        'aging_method': 'due_date',
    }

    def pre_print_report(self, cr, uid, ids, data, context=None):
        data = super(AccountAgedTrialBalance, self).pre_print_report(
            cr, uid, ids, data, context)
        # will be used to attach the report on the main account
        data['ids'] = [data['form']['chart_account_id']]
        vals = self.read(cr, uid, ids,
                         ['detailed_by_invoice',
                          'aging_method'],
                         context=context)[0]
        data['form'].update(vals)
        return data

    def _print_report(self, cr, uid, ids, data, context=None):
        # we update form with display account value
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.account_aged_trial_balance_webkit',
                'datas': data}
