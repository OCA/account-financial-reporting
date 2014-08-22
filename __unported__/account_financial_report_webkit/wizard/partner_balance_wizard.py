# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright Camptocamp SA 2011
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

from openerp.osv import fields, orm


class AccountPartnerBalanceWizard(orm.TransientModel):

    """Will launch partner balance report and pass required args"""

    _inherit = "account.common.balance.report"
    _name = "partner.balance.webkit"
    _description = "Partner Balance Report"

    _columns = {
        'result_selection': fields.selection(
            [('customer', 'Receivable Accounts'),
             ('supplier', 'Payable Accounts'),
             ('customer_supplier', 'Receivable and Payable Accounts')],
            "Partner's", required=True),
        'partner_ids': fields.many2many(
            'res.partner', string='Filter on partner',
            help="Only selected partners will be printed. \
                  Leave empty to print all partners."),
    }

    _defaults = {
        'result_selection': 'customer_supplier',
    }

    def pre_print_report(self, cr, uid, ids, data, context=None):
        data = super(AccountPartnerBalanceWizard, self).\
            pre_print_report(cr, uid, ids, data, context)
        vals = self.read(cr, uid, ids,
                         ['result_selection', 'partner_ids'],
                         context=context)[0]
        data['form'].update(vals)
        return data

    def _print_report(self, cursor, uid, ids, data, context=None):
        # we update form with display account value
        data = self.pre_print_report(cursor, uid, ids, data, context=context)

        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.account_report_partner_balance_webkit',
                'datas': data}
