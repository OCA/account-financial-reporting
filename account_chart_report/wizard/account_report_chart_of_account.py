# -*- coding: utf-8 -*-

##############################################################################
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
##############################################################################

from openerp.osv import fields, orm


class ChartOfAccountsReport(orm.TransientModel):
    _name = 'account.print.chart.accounts.report'
    _description = 'Chart of accounts Report'

    domain_char_account = [('parent_id', '=', False)]
    _columns = {
        'chart_account_id': fields.many2one('account.account',
                                            'Chart of Accounts',
                                            help='Select Charts of Accounts',
                                            required=True,
                                            domain=domain_char_account),
    }

    def print_report(self, cr, uid, ids, data, context=None):
        res = self.read(cr, uid, ids, context=context)[0]
        account_id = res["chart_account_id"][0]
        data["form"] = {"id_account": account_id}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.print.chart',
            'datas': data
        }
