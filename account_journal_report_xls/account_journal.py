# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.com). All rights reserved.
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
from openerp import models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    # allow inherited modules to extend the query
    # pylint: disable=old-api7-method-defined
    def _report_xls_query_extra(self, cr, uid, context=None):
        select_extra = ""
        join_extra = ""
        where_extra = ""
        return (select_extra, join_extra, where_extra)

    # allow inherited modules to add document references
    # pylint: disable=old-api7-method-defined
    def _report_xls_document_extra(self, cr, uid, context):
        return "''"

    # override list in inherited module to add/drop columns or change order
    # pylint: disable=old-api7-method-defined
    def _report_xls_fields(self, cr, uid, context=None):
        res = [
            'move_name',         # account.move,name
            'move_date',         # account.move,date
            'acc_code',          # account.account,code
        ]
        if context.get('print_by') == 'fiscalyear':
            res += [
                'period',        # account.period,code or name
            ]
        res += [
            'partner_name',      # res.partner,name
            'aml_name',          # account.move.line,name
            'tax_code',          # account.tax.code,code
            'tax_amount',        # account.move.line,tax_amount
            'debit',             # account.move.line,debit
            'credit',            # account.move.line,credit
            'balance',           # debit-credit
            'docname',           # origin document if any
            # 'date_maturity',     # account.move.line,date_maturity
            # 'reconcile',         # account.move.line,reconcile_id.name
            # 'reconcile_partial',
            # account.move.line,reconcile_partial_id.name
            # 'partner_ref',       # res.partner,ref
            # 'move_ref',          # account.move,ref
            # 'move_id',           # account.move,id
            # 'acc_name',          # account.account,name
            # 'journal',           # account.journal,name
            # 'journal_code',      # account.journal,code
            # 'analytic_account',       # account.analytic.account,name
            # 'analytic_account_code',  # account.analytic.account,code
        ]
        return res

    # Change/Add Template entries
    # pylint: disable=old-api7-method-defined
    def _report_xls_template(self, cr, uid, context=None):
        """
        Template updates, e.g.

        my_change = {
            'move_name':{
                'header': [1, 20, 'text', _render("_('My Move Title')")],
                'lines': [1, 0, 'text', _render("l['move_name'] != '/' and
                l['move_name'] or ('*'+str(l['move_id']))")],
                'totals': [1, 0, 'text', None]},
        }
        return my_change
        """
        return {}
