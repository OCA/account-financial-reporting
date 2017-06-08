# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
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

from openerp import models, fields


class IntrastatRegion(models.Model):
    _name = 'intrastat.region'
    _description = "Intrastat Region"

    code = fields.Char(string='Code', required=True)
    country_id = fields.Many2one(
        'res.country', string='Country', required=True)
    name = fields.Char(string='Name', translate=True)
    description = fields.Char(string='Description')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'intrastat.region'))

    _sql_constraints = [
        ('intrastat_region_code_unique',
         'UNIQUE(code, country_id)',
         'Code must be unique.')]
