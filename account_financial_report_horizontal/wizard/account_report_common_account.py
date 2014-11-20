# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2013 Agile Business Group sagl
#    (<http://www.agilebg.com>) (<lorenzo.battistini@agilebg.com>)
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


class account_common_account_report(orm.TransientModel):
    _name = 'account_financial_report_horizontal.common.account.report'
    _description = 'Account Common Account Report'
    _inherit = "account_financial_report_horizontal.common.report"
    _columns = {
        'display_account': fields.selection([
            ('bal_all', 'All'), ('bal_movement', 'With movements'),
            ('bal_solde', 'With balance is not equal to 0'),
        ], 'Display accounts', required=True),

    }
    _defaults = {
        'display_account': 'bal_all',
    }

    def pre_print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data['form'].update(self.read(
            cr, uid, ids, ['display_account'], context=context)[0])
        data['form']['lang'] = self.pool.get('res.users').browse(
            cr, uid, uid, context).lang
        return data
