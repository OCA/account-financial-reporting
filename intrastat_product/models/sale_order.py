# -*- coding: utf-8 -*-
##############################################################################
#
#    Intrastat Product module for Odoo
#    Copyright (C) 2010-2015 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
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

from openerp import models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _prepare_invoice(self, order, lines):
        '''Copy destination country to invoice'''
        invoice_vals = super(SaleOrder, self)._prepare_invoice(
            order, lines)
        invoice_vals['src_dest_country_id'] = \
            order.partner_shipping_id.country_id.id or False
        invoice_vals['incoterm_id'] = order.incoterm.id or False
        return invoice_vals
