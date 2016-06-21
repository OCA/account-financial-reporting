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


class IntrastatTransaction(models.Model):
    _name = 'intrastat.transaction'
    _description = "Intrastat Transaction"
    _order = 'code'
    _rec_name = 'display_name'

    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')
    display_name = fields.Char(
        compute='_compute_display_name', string="Display Name", readonly=True,
        store=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'intrastat.transaction'))

    @api.multi
    @api.depends('code', 'description')
    def _compute_display_name(self):
        for this in self:
            display_name = this.code
            if this.description:
                display_name += ' ' + this.description
            this.display_name = len(display_name) > 55 \
                and display_name[:55] + '...' \
                or display_name

    _sql_constraints = [(
        'intrastat_transaction_code_unique',
        'UNIQUE(code, company_id)',
        'Code must be unique.')]
