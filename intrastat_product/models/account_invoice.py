# -*- coding: utf-8 -*-
##############################################################################
#
#    Intrastat Product module for Odoo
#    Copyright (C) 2011-2016 Akretion (http://www.akretion.com)
#    Copyright (C) 2009-2016 Noviat (http://www.noviat.com)
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


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    incoterm_id = fields.Many2one(
        'stock.incoterms', string='Incoterm',
        help="International Commercial Terms are a series of predefined "
             "commercial terms used in international transactions.")
    intrastat_transaction_id = fields.Many2one(
        'intrastat.transaction', string='Intrastat Transaction Type',
        default=lambda self: self._default_intrastat_transaction_id(),
        ondelete='restrict',
        help="Intrastat nature of transaction")
    intrastat_transport_id = fields.Many2one(
        'intrastat.transport_mode', string='Intrastat Transport Mode',
        ondelete='restrict')
    src_dest_country_id = fields.Many2one(
        'res.country', string='Origin/Destination Country',
        ondelete='restrict')
    src_dest_region_id = fields.Many2one(
        'intrastat.region', string='Origin/Destination Region',
        default=lambda self: self._default_src_dest_region_id(),
        help="Origin/Destination Region."
             "\nThis field is used for the Intrastat Declaration.",
        ondelete='restrict')
    intrastat_country = fields.Boolean(
        compute='_compute_intrastat_country',
        store=True, string='Intrastat Country', readonly=True)
    intrastat = fields.Char(
        string='Intrastat Declaration',
        related='company_id.intrastat', readonly=True)

    @api.multi
    @api.depends('src_dest_country_id', 'partner_id.country_id')
    def _compute_intrastat_country(self):
        for inv in self:
            country = inv.src_dest_country_id \
                or inv.partner_id.country_id
            inv.intrastat_country = country.intrastat

    @api.model
    def _default_intrastat_transaction_id(self):
        company = self.env['res.company']
        company_id = company._company_default_get('account.invoice')
        company = company.browse(company_id)
        inv_type = self._context.get('type')
        if inv_type == 'out_invoice':
            return company.intrastat_transaction_out_invoice
        elif inv_type == 'out_refund':
            return company.intrastat_transaction_out_refund
        elif inv_type == 'in_invoice':
            return company.intrastat_transaction_in_invoice
        elif inv_type == 'in_refund':
            return company.intrastat_transaction_in_refund
        else:
            return self.env['intrastat.transaction']

    @api.model
    def _default_src_dest_region_id(self):
        rco = self.env['res.company']
        company_id = rco._company_default_get('account.invoice')
        company = rco.browse(company_id)
        return company.intrastat_region_id

    @api.multi
    def onchange_partner_id(
            self, type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False):
        res = super(AccountInvoice, self).onchange_partner_id(
            type, partner_id, date_invoice=date_invoice,
            payment_term=payment_term, partner_bank_id=partner_bank_id,
            company_id=company_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            res['value']['src_dest_country_id'] = partner.country_id.id
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    hs_code_id = fields.Many2one(
        'hs.code', string='Intrastat Code', ondelete='restrict')

    @api.multi
    def product_id_change(
            self, product, uom_id, qty=0, name='', type='out_invoice',
            partner_id=False, fposition_id=False, price_unit=False,
            currency_id=False, company_id=None):
        res = super(AccountInvoiceLine, self).product_id_change(
            product, uom_id, qty=qty, name=name, type=type,
            partner_id=partner_id, fposition_id=fposition_id,
            price_unit=price_unit, currency_id=currency_id,
            company_id=company_id)

        if product:
            product = self.env['product.product'].browse(product)
            hs_code = product.product_tmpl_id.get_hs_code_recursively()
            if hs_code:
                res['value']['hs_code_id'] = hs_code.id
            else:
                res['value']['hs_code_id'] = False
        return res
