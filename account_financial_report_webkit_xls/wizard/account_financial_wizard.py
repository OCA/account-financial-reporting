# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Addons modules by CLEARCORP S.A.
#    Copyright (C) 2009-TODAY CLEARCORP S.A. (<http://clearcorp.co.cr>).
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

from openerp.osv import orm


class account_financial_wizard(orm.TransientModel):

    _inherit = 'accounting.report'

    def xls_export(self, cr, uid, ids, context=None):
        return self.check_report(cr, uid, ids, context=context)

    def _print_report(self, cr, uid, ids, data, context=None):
        context = context or {}
        if context.get('xls_export'):
            data['form'].update(
                self.read(cr, uid, ids, [
                    'date_from_cmp',  'debit_credit', 'date_to_cmp',
                    'fiscalyear_id_cmp', 'period_from_cmp', 'period_to_cmp',
                    'filter_cmp', 'account_report_id', 'enable_filter',
                    'label_filter', 'target_move'], context=context)[0])
            # They use "data" that is required in the module method check_
            # report account_common_report and "datas" are used to send
            # data to py wizard that exports to excell
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.report_financial_xls',
                'datas': data,
                'data': data}
        else:
            return super(account_financial_wizard, self)._print_report(
                cr, uid, ids, data, context=context)
