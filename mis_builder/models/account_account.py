# -*- coding: utf-8 -*-
#
##############################################################################
#
#     Authors: Adrien Peiffer
#    Copyright (c) 2015 Acsone SA/NV (http://www.acsone.eu)
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


class account_account(orm.Model):
    _inherit = 'account.account'

    def _compute(self, cr, uid, ids, field_names, arg=None, context=None,
                 query='', query_params=()):
        return self.__compute(cr, uid, ids, field_names, arg=arg,
                              context=context, query=query,
                              query_params=query_params)
