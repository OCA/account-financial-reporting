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

from openerp import fields, models, api


class ChartOfAccountsReport(models.TransientModel):
    _name = 'account.print.chart.accounts.report'
    _description = 'Chart of accounts Report'

    chart_account_id = fields.Many2one(
        'account.account',
        'Chart of Accounts',
        help='Select Charts of Accounts',
        required=True,
        domain=([('parent_id', '=', False)]))

    @api.multi
    def print_report(self, data):
        account_id = self.chart_account_id.id
        data["form"] = {"id_account": account_id}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.print.chart',
            'datas': data
        }
