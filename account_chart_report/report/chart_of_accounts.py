# -*- coding: utf-8 -*-

###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Savoir-faire Linux (<www.savoirfairelinux.com>).
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
###############################################################################

from openerp.report import report_sxw


class AccountChar(report_sxw.rml_parse):
    _name = 'report.account.print.chart'

    def __init__(self, cr, uid, name, context=None):
        super(AccountChar, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            "get_lst_account": self._get_lst_account,
            "cr": cr,
            "uid": uid,
            "actual_context": context,
        })

    def _get_lst_account(self, cr, uid, account_id, context):
        account_obj = self.pool['account.account']
        actual_account = account_obj.browse(cr, uid, account_id,
                                            context=context)
        lst_account = []
        self._fill_list_account_with_child(lst_account, actual_account)
        return lst_account

    def _fill_list_account_with_child(self, lst_account, account):
        # no more child
        lst_account.append(account)
        if not account.child_id:
            return
        for child in account.child_id:
            self._fill_list_account_with_child(lst_account, child)


report_sxw.report_sxw(
    'report.account.print.chart',
    'account.account',
    'account_chart_report/report/chart_of_accounts.rml',
    parser=AccountChar,
)
