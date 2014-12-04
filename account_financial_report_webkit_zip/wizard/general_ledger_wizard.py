# -*- encoding: utf-8 -*-
##############################################################################
#
#    Authors: Matthieu Dietrich
#    Copyright Camptocamp SA 2014
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


class AccountReportGeneralLedgerWizard(orm.TransientModel):
    _inherit = 'general.ledger.webkit'

    def zip_export(self, cr, uid, ids, context=None):
        return self.check_report(cr, uid, ids, context=context)

    def _print_report(self, cr, uid, ids, data, context=None):
        context = context or {}
        if context.get('zip_export'):
            data = self.pre_print_report(cr, uid, ids, data, context=context)
            return {'type': 'ir.actions.report.xml',
                    'report_name': 'account.account_report_general_ledger_zip',
                    'datas': data}
        else:
            return super(AccountReportGeneralLedgerWizard, self)._print_report(
                cr, uid, ids, data, context=context
            )
