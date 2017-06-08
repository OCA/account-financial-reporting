# -*- coding: utf-8 -*-
##############################################################################
#
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


class HSCode(models.Model):
    _name = "hs.code"
    _description = "H.S. Code"
    _order = "local_code"
    _rec_name = "display_name"

    hs_code = fields.Char(
        string='H.S. Code', compute='_compute_hs_code', readonly=True,
        help="Harmonized System code (6 digits). Full list is "
        "available from the World Customs Organisation, see "
        "http://www.wcoomd.org")
    description = fields.Char(
        'Description', translate=True,
        help="Short text description of the H.S. category")
    display_name = fields.Char(
        compute='_compute_display_name', string="Display Name",
        store=True, readonly=True)
    local_code = fields.Char(
        string='Local Code', required=True,
        help="Code used for the national Import/Export declaration. "
        "The national code starts with the 6 digits of the H.S. and often "
        "has a few additional digits to extend the H.S. code.")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True, required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'hs.code'))
    product_categ_ids = fields.One2many(
        'product.category', 'hs_code_id', string='Product Categories')
    product_tmpl_ids = fields.One2many(
        'product.template', 'hs_code_id', string='Products')

    @api.multi
    @api.depends('local_code')
    def _compute_hs_code(self):
        for this in self:
            this.hs_code = this.local_code and this.local_code[:6]

    @api.multi
    @api.depends('local_code', 'description')
    def _compute_display_name(self):
        for this in self:
            display_name = this.local_code
            if this.description:
                display_name += ' ' + this.description
            this.display_name = len(display_name) > 55 \
                and display_name[:55] + '...' \
                or display_name

    _sql_constraints = [
        ('local_code_company_uniq', 'unique(local_code, company_id)',
         'This code already exists for this company !'),
        ]

    @api.model
    def create(self, vals):
        if vals.get('local_code'):
            vals['local_code'] = vals['local_code'].replace(' ', '')
        return super(HSCode, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('local_code'):
            vals['local_code'] = vals['local_code'].replace(' ', '')
        return super(HSCode, self).write(vals)
