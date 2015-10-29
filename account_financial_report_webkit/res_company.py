# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2009-2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm


class res_company(orm.Model):
    _inherit = 'res.company'

    def _get_first_special_period(self, cr, uid, context=None):
        first_special = self.pool.get('account.period').search(cr, uid,
              [('special', '=', True)], order='date_start ASC', limit=1)
        return first_special and first_special[0] or False

    _columns = {
        'first_special_period_id': fields.many2one(
            'account.period', 'First Special Period',
            domain=[('special', '=', True)],
            help="When specified, the accounting reports "
                 "will consider this period as the start period "
                 "for the calculation of opening balances.")
    }

    _defaults = {
        'first_special_period_id': _get_first_special_period,
    }
