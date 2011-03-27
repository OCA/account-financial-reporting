# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010-2011 Akretion (http://www.akretion.com/) All Rights Reserved
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


class report_intrastat_type(osv.osv):
    _name = "report.intrastat.type"
    _description = "Intrastat type"
    _columns = {
        'name': fields.char('Name',size=64,help="Name which appear when you select the Intrastat type on the invoice."),
        'active' : fields.boolean('Active', help="The active field allows you to hide the Intrastat type without deleting it."),
        'company_id': fields.many2one('res.company', 'Company'),
        'type': fields.selection([('import', 'Import'),('export', 'Export'), ('other', 'Other')], 'Value', required=True, help="If 'Import' is selected, the corresponding invoices will be selected for the 'Intrastat Import' reports. Same for 'Export'. If 'Other' is selected, the corresponding invoices will NOT be selected in any Intrastat report ; so you should choose it for an invoice only in very particular cases."),
        'intrastat_only': fields.boolean('Intrastat only', help="An invoice which has an Intrastat type which is 'Intrastat only' = true is not a real invoice i.e. once created it won't have an invoice number nor corresponding accounting entries. It follows a different path in the invoice workflow and it's state once created is called 'legal intrastat'. So the purpose of an 'intrastat only' invoice is to add entries to the Intrastat report without impacting anything else. This is used for example for a repair under warranty : nothing is invoiced to the customer, but it creates a movement of goods which should be part of the Intrastat report with a certain value.")
        }

    _defaults = {
        'active': lambda *a: 1,
    }

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        if not args:
            args=[]

        if context is None:
            context={}

        ids = []

        if context.get('type', False) == 'out_invoice':
            args = args+['|',('type','=','export'), ('type','=','other')]

        if context.get('type', False) == 'in_invoice':
            args = args+['|',('type','=','import'), ('type','=','other')]

        if context.get('type', False) == 'in_refund':
            args = args+['|',('type','=','export'), ('type','=','other')]

        if context.get('type', False) == 'out_refund':
            args = args+['|',('type','=','import'), ('type','=','other')]

        return super(report_intrastat_type,self).search(cr, user, args, offset, limit, order, context=context, count=count)

report_intrastat_type()

