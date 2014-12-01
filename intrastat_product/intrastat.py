# -*- encoding: utf-8 -*-
##############################################################################
#
#    Intrastat Product module for OpenERP
#    Copyright (C) 2004-2009 Tiny SPRL (http://tiny.be)
#    Copyright (C) 2010-2014 Akretion (http://www.akretion.com)
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

from openerp import models, fields, api, _
from openerp.exceptions import Warning


class ReportIntrastatCode(models.Model):
    _name = "report.intrastat.code"
    _description = "H.S. Code"
    _order = "name"

    name = fields.Char(
        string='H.S. code', required=True,
        help="Full length Harmonized System code (digits only). Full list is "
        "available from the World Customs Organisation, see "
        "http://www.wcoomd.org")
    description = fields.Char(
        'Description', help="Short text description of the H.S. category")

    @api.multi
    @api.depends('name', 'description')
    def name_get(self):
        res = []
        for code in self:
            name = code.name
            if code.description:
                name = u'%s %s' % (name, code.description)
            res.append((code.id, name))
        return res

    @api.constrains('name')
    def _hs_code(self):
        if self.name and not self.name.isdigit():
            raise Warning(
                _("H.S. codes should only contain digits. It is not the case "
                    "of H.S. code '%s'.") % self.name)

    _sql_constraints = [(
        'hs_code_uniq',
        'unique(name)',
        'This H.S. code already exists in Odoo !'
        )]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    intrastat_id = fields.Many2one(
        'report.intrastat.code', string='Intrastat Code',
        help="Code from the Harmonised System. Nomenclature is "
        "available from the World Customs Organisation, see "
        "http://www.wcoomd.org/. Some countries have made their own "
        "extensions to this nomenclature.")
    origin_country_id = fields.Many2one(
        'res.country', string='Country of Origin',
        help="Country of origin of the product i.e. product "
        "'made in ____'. If you have different countries of origin "
        "depending on the supplier from which you purchased the product, "
        "leave this field empty and use the equivalent field on the "
        "'product supplier info' form.")


class ProductCategory(models.Model):
    _inherit = "product.category"

    intrastat_id = fields.Many2one(
        'report.intrastat.code', string='Intrastat Code',
        help="Code from the Harmonised System. If this code is not "
        "set on the product itself, it will be read here, on the "
        "related product category.")
