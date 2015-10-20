# -*- encoding: utf-8 -*-
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

from openerp import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class L10nBeIntrastatProductDeclaration(models.Model):
    _name = 'l10n.be.intrastat.product.declaration'
    _description = "Intrastat Product Declaration for Belgium"
    _inherit = ['intrastat.product.declaration', 'mail.thread']

    computation_line_ids = fields.One2many(
        'l10n.be.intrastat.product.computation.line',
        'parent_id', string='Intrastat Product Computation Lines',
        states={'done': [('readonly', True)]})
    declaration_line_ids = fields.One2many(
        'l10n.be.intrastat.product.declaration.line',
        'parent_id', string='Intrastat Product Declaration Lines',
        states={'done': [('readonly', True)]})

    def _get_region(self, inv_line):
        """
        Logic copied from standard addons, l10n_be_intrastat module:

        If purchase, comes from purchase order, linked to a location,
        which is linked to the warehouse.

        If sales, the sale order is linked to the warehouse.
        If sales, from a delivery order, linked to a location,
        which is linked to the warehouse.

        If none found, get the company one.
        """
        region = False
        if inv_line.invoice_id.type in ('in_invoice', 'in_refund'):
            po_lines = self.env['purchase.order.line'].search(
                [('invoice_lines', 'in', inv_line.id)])
            if po_lines:
                po = po_lines.order_id
                region = self.env['stock.warehouse'].get_region_from_location(
                    po.location_id)
        elif inv_line.invoice_id.type in ('out_invoice', 'out_refund'):
            so_lines = self.env['sale.order.line'].search(
                [('invoice_lines', 'in', inv_line.id)])
            if so_lines:
                so = so_lines.order_id
                region = so.warehouse_id.region_id
        if not region:
            if self.company_id.intrastat_region_id:
                region = self.company_id.intrastat_region_id
            else:
                msg = _(
                    "The Intrastat Region of the Company is not set, "
                    "please configure it first.")
                self._company_warning(msg)
        return region

    def _update_computation_line_vals(self, inv_line, line_vals):
        if self.company_country_code == 'be':
            region = self._get_region(inv_line)
            line_vals.update({
                'region_id': region.id,
                })
            if self._extended and self.company_country_code == 'be':
                incoterm = self._get_incoterm(inv_line)
                line_vals.update({
                    'incoterm_id': incoterm.id,
                    })
        else:
            super(L10nBeIntrastatProductDeclaration, self
                  )._update_computation_line_vals(inv_line, line_vals)

    @api.model
    def group_line_hashcode(self, computation_line):
        hashcode = super(
            L10nBeIntrastatProductDeclaration, self
            ).group_line_hashcode(computation_line)
        # TODO:
        # move region_id to intrastat_product since
        # the region fields is used by +/- 30% of the
        # intrastat countries
        hashcode += '-%s' % computation_line.region_id.id or False
        return hashcode


class L10nBeIntrastatProductComputationLine(models.Model):
    _name = 'l10n.be.intrastat.product.computation.line'
    _inherit = 'intrastat.product.computation.line'

    parent_id = fields.Many2one(
        'l10n.be.intrastat.product.declaration',
        string='Intrastat Product Declaration',
        ondelete='cascade', readonly=True)
    region_id = fields.Many2one(
        'intrastat.region', string='Intrastat Region')
    declaration_line_id = fields.Many2one(
        'l10n.be.intrastat.product.declaration.line',
        string='Declaration Line', readonly=True)


class L10nBeIntrastatProductDeclarationLine(models.Model):
    _name = 'l10n.be.intrastat.product.declaration.line'
    _inherit = 'intrastat.product.declaration.line'

    parent_id = fields.Many2one(
        'l10n.be.intrastat.product.declaration',
        string='Intrastat Product Declaration',
        ondelete='cascade', readonly=True)
    region_id = fields.Many2one(
        'intrastat.region', string='Intrastat Region')
    computation_line_ids = fields.One2many(
        'l10n.be.intrastat.product.computation.line', 'declaration_line_id',
        string='Computation Lines', readonly=True)

    @api.model
    def _prepare_grouped_fields(self, computation_line, fields_to_sum):
        vals = super(
            L10nBeIntrastatProductDeclarationLine, self
            )._prepare_grouped_fields(computation_line, fields_to_sum)
        vals.update({
            'region_id': computation_line.region_id.id,
            })
        return vals
