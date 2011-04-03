# -*- encoding: utf-8 -*-
##############################################################################
#
#    Report intrastat base module for OpenERP
#    Copyright (C) 2009-2011 Akretion (http://www.akretion.com/) All Rights Reserved
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

from osv import osv, fields
from tools.translate import _

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    _columns = {
        'intrastat_type_id': fields.many2one('report.intrastat.type', 'Intrastat Type',select=True,readonly=True, states={'draft':[('readonly',False)]}),
        'state': fields.selection([
            ('draft','Draft'),
            ('legal_intrastat','Legal Intrastat'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Open'),
            ('paid','Done'),
            ('cancel','Cancelled')
        ],'State', select=True, readonly=True),
        'intrastat_only': fields.boolean('Intrastat Only'),
    }

    def intrastat_type_id_change(self, cr, uid, ids, intrastat_type_id):
        if intrastat_type_id:
            intrastat_only = self.pool.get('report.intrastat.type').browse(cr, uid, intrastat_type_id).intrastat_only
            return {'value': {'intrastat_only': intrastat_only}}

account_invoice()

