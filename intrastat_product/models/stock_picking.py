# -*- coding: utf-8 -*-
##############################################################################
#
#    Intrastat Product module for Odoo
#    Copyright (C) 2011-2015 Akretion (http://www.akretion.com)
#    Copyright (C) 2009-2015 Noviat (http://www.noviat.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Luc de Meyer <info@noviat.com>
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

from openerp import models, fields, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    intrastat_transport_id = fields.Many2one(
        'intrastat.transport_mode', string='Transport Mode',
        help="This information is used in Intrastat reports")
    intrastat = fields.Char(related='company_id.intrastat')

    @api.model
    def _create_invoice_from_picking(self, picking, vals):
        """ Copy data from picking to invoice. """
        vals['intrastat_transport_id'] = picking.intrastat_transport_id.id
        if picking.partner_id and picking.partner_id.country_id:
            vals['src_dest_country_id'] = picking.partner_id.country_id.id
        region = picking.location_id.get_intrastat_region()
        if region:
            vals['src_dest_region_id'] = region.id
        return super(StockPicking, self)._create_invoice_from_picking(
            picking, vals)
