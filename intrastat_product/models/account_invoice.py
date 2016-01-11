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


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    incoterm_id = fields.Many2one(
        'stock.incoterms', string='Incoterm',
        help="International Commercial Terms are a series of predefined "
             "commercial terms used in international transactions.")
    intrastat_transaction_id = fields.Many2one(
        'intrastat.transaction', string='Intrastat Transaction Type',
        default=lambda self: self._default_intrastat_transaction(),
        ondelete='restrict',
        help="Intrastat nature of transaction")
    intrastat_transport_id = fields.Many2one(
        'intrastat.transport_mode', string='Intrastat Transport Mode',
        ondelete='restrict')
    src_dest_country_id = fields.Many2one(
        'res.country', string='Origin/Destination Country',
        ondelete='restrict')
    intrastat_country = fields.Boolean(
        related='src_dest_country_id.intrastat',
        store=True, string='Intrastat Country', readonly=True)
    intrastat = fields.Char(
        string='Intrastat Declaration',
        related='company_id.intrastat', readonly=True)

    @api.model
    def _default_intrastat_transaction(self):
        """ placeholder for localisation modules """
        return self.env['intrastat.transaction'].browse([])

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
