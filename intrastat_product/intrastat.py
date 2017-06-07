# -*- encoding: utf-8 -*-
##############################################################################
#
#    Intrastat Product module for Odoo
#    Copyright (C) 2011-2015 Akretion (http://www.akretion.com)
#    Copyright (C) 2015 Noviat (http://www.noviat.com)
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

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


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


class HSCode(models.Model):
    _inherit = "hs.code"

    intrastat_unit_id = fields.Many2one(
        'intrastat.unit', string='Intrastat Supplementary Unit')

    @api.constrains('local_code')
    def _hs_code(self):
        if self.company_id.country_id.intrastat:
            if not self.local_code.isdigit():
                raise ValidationError(
                    _("Intrastat Codes should only contain digits. "
                      "This is not the case for code '%s'.")
                    % self.local_code)
            if len(self.local_code) != 8:
                raise ValidationError(
                    _("Intrastat Codes should "
                      "contain 8 digits. This is not the case for "
                      "Intrastat Code '%s' which has %d digits.")
                    % (self.local_code, len(self.local_code)))


class IntrastatTransaction(models.Model):
    _name = 'intrastat.transaction'
    _description = "Intrastat Transaction"
    _order = 'code'
    _rec_name = 'display_name'

    @api.one
    @api.depends('code', 'description')
    def _compute_display_name(self):
        display_name = self.code
        if self.description:
            display_name += ' ' + self.description
        self.display_name = len(display_name) > 55 \
            and display_name[:55] + '...' \
            or display_name

    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')
    display_name = fields.Char(
        compute='_compute_display_name', string="Display Name", readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'intrastat.transaction'))

    _sql_constraints = [(
        'intrastat_transaction_code_unique',
        'UNIQUE(code, company_id)',
        'Code must be unique.')]


class IntrastatTransportMode(models.Model):
    _name = 'intrastat.transport_mode'
    _description = "Intrastat Transport Mode"
    _rec_name = 'display_name'
    _order = 'code'

    @api.one
    @api.depends('name', 'code')
    def _display_name(self):
        self.display_name = '%s. %s' % (self.code, self.name)

    display_name = fields.Char(
        string='Display Name', compute='_display_name', store=True,
        readonly=True)
    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Name', required=True, translate=True)
    description = fields.Char(string='Description', translate=True)

    _sql_constraints = [(
        'intrastat_transport_code_unique',
        'UNIQUE(code)',
        'Code must be unique.')]
