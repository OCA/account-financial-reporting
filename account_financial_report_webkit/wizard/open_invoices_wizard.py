# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright Camptocamp SA 2012
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


class AccountReportOpenInvoicesWizard(orm.TransientModel):

    """Will launch partner ledger report and pass required args"""

    _inherit = "partners.ledger.webkit"
    _name = "open.invoices.webkit"
    _description = "Open Invoices Report"

    _columns = {
        'group_by_currency': fields.boolean('Group Partner by currency'),
        'until_date': fields.date(
            "Clearance date",
            required=True,
            help="""The clearance date is essentially a tool used for debtors
            provisionning calculation.

By default, this date is equal to the the end date (ie: 31/12/2011 if you
select fy 2011).

By amending the clearance date, you will be, for instance, able to answer the
question : 'based on my last year end debtors open invoices, which invoices
are still unpaid today (today is my clearance date)?'
""")}

    def _check_until_date(self, cr, uid, ids, context=None):
        def get_key_id(obj, field):
            return obj.get(field) and obj[field][0] or False

        obj = self.read(cr, uid, ids[0], [
                        'fiscalyear_id', 'period_to', 'date_to', 'until_date'],
                        context=context)
        min_date = self.default_until_date(cr, uid, ids,
                                           get_key_id(obj, 'fiscalyear_id'),
                                           get_key_id(obj, 'period_to'),
                                           obj['date_to'],
                                           context=context)
        if min_date and obj['until_date'] < min_date:
            return False
        return True

    _constraints = [
        (_check_until_date, 'Clearance date must be the very last date of the \
        last period or later.', ['until_date']),
    ]

    def default_until_date(self, cr, uid, ids, fiscalyear_id=False,
                           period_id=False, date_to=False, context=None):
        res_date = False
        # first priority: period or date filters
        if period_id:
            res_date = self.pool.get('account.period').read(
                cr, uid, period_id, ['date_stop'],
                context=context)['date_stop']
        elif date_to:
            res_date = date_to
        elif fiscalyear_id:
            res_date = self.pool.get('account.fiscalyear').read(
                cr, uid, fiscalyear_id, ['date_stop'],
                context=context)['date_stop']
        return res_date

    def onchange_fiscalyear(self, cr, uid, ids, fiscalyear=False,
                            period_id=False, date_to=False, until_date=False,
                            context=None):
        res = {'value': {}}
        res['value']['until_date'] = self.default_until_date(
            cr, uid, ids,
            fiscalyear_id=fiscalyear,
            period_id=period_id,
            date_to=date_to,
            context=context)
        return res

    def onchange_date_to(self, cr, uid, ids, fiscalyear=False, period_id=False,
                         date_to=False, until_date=False, context=None):
        res = {'value': {}}
        res['value']['until_date'] = self.default_until_date(
            cr, uid, ids,
            fiscalyear_id=fiscalyear,
            period_id=period_id,
            date_to=date_to,
            context=context)
        return res

    def onchange_period_to(self, cr, uid, ids, fiscalyear=False,
                           period_id=False, date_to=False, until_date=False,
                           context=None):
        res = {'value': {}}
        res['value']['until_date'] = self.default_until_date(
            cr, uid, ids,
            fiscalyear_id=fiscalyear,
            period_id=period_id,
            date_to=date_to,
            context=context)
        return res

    def onchange_filter(self, cr, uid, ids, filter='filter_no',
                        fiscalyear_id=False, context=None):
        res = super(AccountReportOpenInvoicesWizard, self).onchange_filter(
            cr, uid, ids, filter=filter, fiscalyear_id=fiscalyear_id,
            context=context)
        if res.get('value', False):
            res['value']['until_date'] = self.default_until_date(
                cr, uid, ids,
                fiscalyear_id=fiscalyear_id,
                period_id=res['value'].get('period_to', False),
                date_to=res['value'].get('date_to', False),
                context=context)
        return res

    def pre_print_report(self, cr, uid, ids, data, context=None):
        data = super(AccountReportOpenInvoicesWizard, self).pre_print_report(
            cr, uid, ids, data, context=context)
        vals = self.read(cr, uid, ids,
                         ['until_date', 'group_by_currency'],
                         context=context)[0]
        data['form'].update(vals)
        return data

    def _print_report(self, cr, uid, ids, data, context=None):
        # we update form with display account value
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.account_report_open_invoices_webkit',
                'datas': data}
