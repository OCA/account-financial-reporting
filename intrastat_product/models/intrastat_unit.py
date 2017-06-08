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

from openerp import models, fields


class IntrastatUnit(models.Model):
    _name = 'intrastat.unit'
    _description = 'Intrastat Supplementary Units'

    name = fields.Char(
        string='Name', required=True)
    description = fields.Char(
        string='Description', required=True)
    uom_id = fields.Many2one(
        'product.uom', string='Regular UoM',
        help="Select the regular Unit of Measure of Odoo that corresponds "
        "to this Intrastat Supplementary Unit.")
    active = fields.Boolean(
        string='Active', default=True)
