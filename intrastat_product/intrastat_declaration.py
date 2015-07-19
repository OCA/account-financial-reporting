# -*- encoding: utf-8 -*-
##############################################################################
#
#    Intrastat Product module for Odoo
#    Copyright (C) 2011-2015 Akretion (http://www.akretion.com)
#    Copyright (C) 2011-2015 Noviat (http://www.noviat.com)
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
from openerp.exceptions import Warning, RedirectWarning, ValidationError
import openerp.addons.decimal_precision as dp
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from lxml import etree
import logging
_logger = logging.getLogger(__name__)


class IntrastatProductDeclaration(models.Model):
    _name = 'intrastat.product.declaration'
    _description = "Intrastat Product Report Base Object"
    _rec_name = 'year_month'
    _inherit = ['mail.thread', 'report.intrastat.common']
    _order = 'year_month desc, type, revision'
    _track = {
        'state': {
            'intrastat_product.declaration_done':
            lambda self, cr, uid, obj, ctx=None: obj['state'] == 'done',
            }
        }

    @api.model
    def _get_type(self):
        res = []
        company = self.env.user.company_id
        arrivals = company.intrastat_arrivals
        dispatches = company.intrastat_dispatches
        if arrivals != 'exempt':
            res.append(('arrivals', _('Declaration for Arrivals')))
        if dispatches != 'exempt':
            res.append(('dispatches', _('Declaration for Dispatches')))
        return res

    @api.model
    def _get_reporting_level(self):
        return [
            ('standard', _('Standard')),
            ('extended', _('Extended'))]

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'arrivals':
            self.reporting_level = \
                self.company_id.intrastat_arrivals == 'extended' \
                and 'extended' or 'standard'
        if self.type == 'dispatches':
            self.reporting_level = \
                self.company_id.intrastat_dispatches == 'extended' \
                and 'extended' or 'standard'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    @api.model
    def _get_year(self):
        if datetime.now().month == 1:
            return datetime.now().year - 1
        else:
            return datetime.now().year

    @api.model
    def _get_month(self):
        if datetime.now().month == 1:
            return 12
        else:
            return datetime.now().month - 1

    @api.model
    def _get_action(self):
        return [
            ('replace', 'Replace'),
            ('append', 'Append'),
            ('nihil', 'Nihil')]

    @api.model
    def _get_default_action(self):
        return 'replace'

    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True,
        default=lambda self: self.env[
            'res.company']._company_default_get('intrastat.product.declaration'))
    year = fields.Integer(
        string='Year', required=True,
        default=_get_year)
    month = fields.Selection([
        (1, '01'),
        (2, '02'),
        (3, '03'),
        (4, '04'),
        (5, '05'),
        (6, '06'),
        (7, '07'),
        (8, '08'),
        (9, '09'),
        (10, '10'),
        (11, '11'),
        (12, '12')
        ], string='Month', required=True,
        default=_get_month)
    year_month = fields.Char(
        compute='_compute_year_month', string='Month', readonly=True,
        track_visibility='always', store=True,
        help="Year and month of the declaration.")
    type = fields.Selection(
        '_get_type', string='Type', required=True,
        states={'done': [('readonly', True)]},
        track_visibility='always', help="Select the declaration type.")
    action = fields.Selection(
        '_get_action',
        string='Action', required=True,
        default=_get_default_action,
        states={'done': [('readonly', True)]},
        track_visibility='onchange')
    revision = fields.Integer(
        string='Revision', default=1,
        states={'done': [('readonly', True)]},
        help="Used to keep track of changes")
    computation_line_ids = fields.One2many(
        'intrastat.product.computation.line',
        'parent_id', string='Intrastat Product Computation Lines',
        states={'done': [('readonly', True)]})
    declaration_line_ids = fields.One2many(
        'intrastat.product.declaration.line',
        'parent_id', string='Intrastat Product Declaration Lines',
        states={'done': [('readonly', True)]})
    num_decl_lines = fields.Integer(
        compute='_compute_numbers', string='Number of Declaration Lines',
        store=True, track_visibility='onchange')
    total_amount = fields.Float(
        compute='_compute_numbers', digits=dp.get_precision('Account'),
        string='Total Amount', store=True,
        help="Total amount in company currency of the declaration.")
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', readonly=True,
        string='Currency')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ], string='State', readonly=True, track_visibility='onchange',
        copy=False, default='draft',
        help="State of the declaration. When the state is set to 'Done', "
        "the parameters become read-only.")
    note = fields.Text(
        string='Notes',
        help="You can add some comments here if you want.")
    reporting_level = fields.Selection(
        '_get_reporting_level',
        string='Reporting Level')
    valid = fields.Boolean(
        compute='_check_validity',
        string='Valid')

    @api.one
    @api.constrains('year')
    def _check_year(self):
        s = str(self.year)
        if len(s) != 4 or s[0] != '2':
            raise ValidationError(
                _("Invalid Year !"))

    _sql_constraints = [
        ('date_uniq',
         'unique(year_month, company_id, type)',
         "A declaration of the same type already exists for this month !"
         "\nYou should update the existing declaration "
         "or change the revision number of this one."),
    ]

    @api.one
    @api.depends('year', 'month')
    def _compute_year_month(self):
        if self.year and self.month:
            self.year_month = '-'.join([str(self.year), format(self.month, '02')])

    @api.one
    @api.depends('month')
    def _check_validity(self):
        """ TO DO: logic based upon computation lines """
        self.valid = True

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = default or {}
        default['revision'] = self.revision + 1
        return super(L10nBeReportIntrastatProduct, self).copy(default)

    def _company_warning(self, msg):
        xmlid_mod = self.pool['ir.model.data']
        action_id = xmlid_mod.xmlid_to_res_id(
            cr, uid, 'base.action_res_company_form')
        raise RedirectWarning(
            msg, action_id,
            _('Go to company configuration screen'))

    def _get_partner_country(self, inv_line):
        country = inv_line.invoice_id.intrastat_country_id \
            or inv_line.invoice_id.partner_id.country_id
        if not country.intrastat:
            country = False
        elif country == self.company_id.country_id:
            country = False
        return country

    def _get_intrastat_transaction(self, inv_line):
        if inv_line.invoice_id.intrastat_transaction_id:
            tr = inv_line.invoice_id.intrastat_transaction_id.code
        else:
            tr = self.env.ref(
                'l10n_be_intrastat_advanced.intrastat_transaction_1')
        return tr

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

    def _get_weight_and_supplunits(self, inv_line):
        line_qty = inv_line.quantity
        product = inv_line.product_id
        invoice = inv_line.invoice_id
        intrastat_unit_id = inv_line.intrastat_id.intrastat_unit_id
        source_uom = inv_line.uos_id
        weight_uom_categ = self._uom_refs['weight_uom_categ']
        kg_uom = self._uom_refs['kg_uom']
        pce_uom_categ = self._uom_refs['pce_uom_categ']
        pce_uom = self._uom_refs['pce_uom']
        weight = suppl_unit_qty = 0.0

        if not source_uom:
            note = "\n" + _(
                "Missing unit of measure on the line with %d "
                "product(s) '%s' on invoice '%s'."
                ) % (line_qty, product.name, invoice.number)
            note += "\n" + _(
                "Please adjust this line manually.")
            self._note += note
            return weight, suppl_unit_qty

        if intrastat_unit_id:
            target_uom = intrastat_unit_id.uom_id
            if not target_uom:
                note = "\n" + _(
                    "Conversion from Intrastat Supplementary Unit '%s' to "
                    "Unit of Measure is not implemented yet."
                    ) % intrastat_unit_id.name
                note += "\n" + _(
                    "Please correct the Intrastat Supplementary Unit "
                    "settingsand regenerate the lines or adjust the lines "
                    "with Intrastat Code 'ùs' manually"
                    ) % intrastat_code
                self._note += note
                return weight, suppl_unit_qty
            if target_uom.categ_id == source_uom.category_id:
                suppl_unit_qty = self.env['product.uom']._compute_qty_obj(
                    source_uom, line_qty, target_uom)
            else:
                note = "\n" + _(
                    "Conversion from unit of measure '%s' to '%s' "
                    "is not implemented yet."
                    ) % (source_uom.name, target_uom.name)
                note += "\n" + _(
                    "Please correct the unit of measure settings and regenerate "
                    "the lines or adjust the impacted lines manually")
                self._note += note
                return weight, suppl_unit_qty

        else:
            if source_uom == kg_uom:
                weight = line_qty
            elif source_uom.category_id == weight_uom_categ:
                weight = self.env['product.uom']._compute_qty_obj(
                    source_uom, line_qty, kg_uom)
            elif source_uom.category_id == pce_uom_categ:
                if not product.weight_net:
                    note = "\n" + _(
                        "Missing net weight on product '%s'."
                        ) % product.name
                    note += "\n" + _(
                        "Please correct the product record and regenerate "
                        "the lines or adjust the impacted lines manually")
                    self._note += note
                    return weight, suppl_unit_qty
                if source_uom == pce_uom:
                    weight = product.weight_net * line_qty
                else:
                    # Here, I suppose that, on the product, the
                    # weight is per PCE and not per uom_id
                    weight = product.weight_net * \
                        self.env['product.uom']._compute_qty_obj(
                            source_uom, line_qty, pce_uom)
            else:
                note = "\n" + _(
                    "Conversion from unit of measure '%s' to 'Kg' "
                    "is not implemented yet."
                    ) % source_uom.name
                note += "\n" + _(
                    "Please correct the unit of measure settings and regenerate "
                    "the lines or adjust the impacted lines manually")
                self._note += note
                return weight, suppl_unit_qty

        return weight, suppl_unit_qty

    def _get_amount(self, inv_line):
        invoice = inv_line.invoice_id
        amount = inv_line.price_subtotal
        if invoice.currency_id.name != 'EUR':
            amount = self.env['res.currency'].with_context(
                date=invoice.date_invoice).compute(
                    invoice.currency_id,
                    self.company_id.currency_id,
                    amount)
        return amount

    def _get_transport(self, inv_line):
        transport = inv_line.invoice.transport_mode_id \
            or self.company_id.intrastat_transport_id
        if not transport:
                msg = _(
                    "The default Intrastat Transport Mode "
                    "of the Company is not set, "
                    "please configure it first.")
                self._company_warning(msg)
        return transport

    def _get_incoterm(self, inv_line):
        incoterm = inv_line.invoice.incoterm_id \
            or self.company_id.incoterm_id
        if not incoterm:
                msg = _(
                    "The default Incoterm "
                    "of the Company is not set, "
                    "please configure it first.")
                self._company_warning(msg)
        return transport

    def _gather_invoices(self):

        decl_lines = []
        start_date = date(self.year, self.month, 1)
        end_date = start_date + relativedelta(day=1, months=+1, days=-1)

        invoices = self.env['account.invoice'].search([
            ('date_invoice', '>=', start_date),
            ('date_invoice', '<=', end_date),
            ('state', 'in', ['open', 'paid']),
            ('intrastat_country', '=', True),
            ('company_id', '=', self.company_id.id)])

        for invoice in invoices:

            if self.type == 'arrivals': 
                if invoice.type in ['out_invoice', 'in_refund']:
                    continue
            else:
                if invoice.type in ['in_invoice', 'out_refund']:
                    continue

            for inv_line in invoice.invoice_line:

                intrastat = inv_line.intrastat_id
                if not intrastat:
                    continue
                if not inv_line.quantity:
                    continue

                partner_country = self._get_partner_country(inv_line)
                if not partner_country:
                    continue

                intrastat_transaction = \
                    self._get_intrastat_transaction(inv_line)

                region = self._get_region(inv_line)

                weight, suppl_unit_qty = self._get_weight_and_supplunits(inv_line)

                amount_company_currency = self._get_amount(inv_line)

                line_vals = {
                    'parent_id': self.id,
                    'invoice_line_id': inv_line.id,
                    'partner_country_id': partner_country.id,
                    'product_id': inv_line.product_id.id,
                    'intrastat_code_id': intrastat.id,
                    'weight': weight,
                    'suppl_unit_qty': suppl_unit_qty,
                    'amount_company_currency': amount_company_currency,
                    'transaction_id': intrastat_transaction.id,
                    'region_id': region.id,
                    'extended': self._extended,
                    }

                # extended declaration
                if self._extended:
                    transport = self._get_transport(inv_line)
                    incoterm = self._get_incoterm(inv_line)
                    line_vals.update({
                        'transport_id': transport.id,
                        'incoterm_id' : incoterm.id,
                        })

                decl_lines.append((0, 0, line_vals))

        return decl_lines

    @api.multi
    def action_gather(self):
        self.ensure_one()
        self._note = ''
        self._uom_refs = {
            'weight_uom_categ': self.env.ref('product.product_uom_categ_kgm'),
            'kg_uom': self.env.ref('product.product_uom_kgm'),
            'pce_uom_categ': self.env.ref('product.product_uom_categ_unit'),
            'pce_uom': self.env.ref('product.product_uom_unit')
            }
        if (self.type == 'arrivals'
                and self.company_id.intrastat_arrivals == 'extended') or (
                self.type == 'dispatches'
                and self.company_id.intrastat_dispatches == 'extended'):
            self._extended = True
        else:
            self._extended = False

        decl_lines_init = [(6, 0, [])]
        decl_lines = decl_lines_init[:]

        decl_lines += self._gather_invoices()

        if decl_lines == decl_lines_init:
            self.action = 'nihil'
            note = "\n" + \
                _("No records found for the selected period !") + '\n' + \
                _("The Declaration Action has been set to 'nihil'.")
            self._note += note

        # To DO: add check on tax cases 46, 48, 84, 86

        self.write({'intrastat_line_ids': decl_lines})

        if self._note:
            note_header = '\n\n>>> ' + str(date.today()) + '\n'
            self.note = (self.note or '') + note_header + self._note
            result_view = self.env.ref(
                'l10n_be_intrastat_advanced.intrastat_result_view')
            return {
                'name': _("Generate lines from invoices: results"),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'intrastat.result.view',
                'view_id': result_view.id,
                'target': 'new',
                'context': dict(self._context, note=self._note),
                'type': 'ir.actions.act_window',
            }

        return True

    @api.multi
    def generate_declaration(self):
        """ generate declaration lines """
        self.ensure_one()
        WIP


class IntrastatProductComputationLine(models.Model):
    _name = 'intrastat.product.computation.line'
    _description = "Intrastat Product Computataion Lines"

    parent_id = fields.Many2one(
        'intrastat.product.declaration',
        string='Intrastat Product Declaration',
        ondelete='cascade', readonly=True)
    company_id = fields.Many2one(
        'res.company', related='parent_id.company_id',
        string="Company", readonly=True)
    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string="Company currency", readonly=True)
    type = fields.Selection(
        related='parent_id.type',
        string='Type',
        readonly=True)
    reporting_level = fields.Selection(
        related='parent_id.reporting_level',
        string='Reporting Level',
        readonly=True)
    valid = fields.Boolean(
        compute='_check_validity',
        string='Valid')
    invoice_line_id = fields.Many2one(
        'account.invoice.line', string='Invoice Line', readonly=True)
    invoice_id = fields.Many2one(
        'account.invoice', related='invoice_line_id.invoice_id',
        string='Invoice', readonly=True)
    declaration_line_id = fields.Many2one(
        'intrastat.product.declaration.line',
        string='Declaration Line', readonly=True)
    src_dest_country_id = fields.Many2one(
        'res.country', string='Country',
        help="Country of Origin/Destination",
        domain=[('intrastat', '=', True)])
    product_id = fields.Many2one(
        'product.product', related='invoice_line_id.product_id',
        string='Product', readonly=True)
    hs_code_id = fields.Many2one(
        'hs.code', string='Intrastat Code')
    intrastat_unit_id = fields.Many2one(
        'intrastat.unit', related='hs_code_id.intrastat_unit_id',
        string='Suppl. Unit', readonly=True,
        help="Intrastat Supplementary Unit")
    weight = fields.Float(
        string='Weight (Kg)',
        digits=dp.get_precision('Stock Weight'))
    suppl_unit_qty = fields.Float(
        string='Suppl. Unit Qty',
        digits=dp.get_precision('Product Unit of Measure'),
        help="Supplementary Units Quantity")
    amount_company_currency = fields.Float(
        string='Fiscal Value',
        digits= dp.get_precision('Account'), required=True,
        help="Amount in company currency to write in the declaration. "
        "Amount in company currency = amount in invoice currency "
        "converted to company currency with the rate of the invoice date.")
    transaction_id = fields.Many2one(
        'intrastat.transaction',
        string='Intrastat Transaction')
    # extended declaration
    transport_id = fields.Many2one(
        'intrastat.transport_mode',
        string='Transport Mode')

    @api.one
    @api.depends('transport_id')
    def _check_validity(self):
        """ TO DO: logic based upon fields """
        self.valid = True

    @api.onchange('product_id')
    def _onchange_product(self):
        self.weight = 0.0
        self.suppl_unit_qty = 0.0
        self.intrastat_code_id = False
        self.intrastat_unit_id = False
        if self.product_id:
            self.intrastat_code_id = product.intrastat_id
            self.intrastat_unit_id = product.intrastat_id.intrastat_unit_id
            if not self.intrastat_unit_id:
                self.weight = self.product_id.weight_net


class IntrastatProductDeclarationLine(models.Model):
    _name = 'intrastat.product.declaration.line'
    _description = "Intrastat Product Declaration Lines"

    parent_id = fields.Many2one(
        'intrastat.product.declaration',
        string='Intrastat Product Declaration',
        ondelete='cascade', readonly=True)
    company_id = fields.Many2one(
        'res.company', related='parent_id.company_id',
        string="Company", readonly=True)
    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string="Company currency", readonly=True)
    type = fields.Selection(
        related='parent_id.type',
        string='Type',
        readonly=True)
    reporting_level = fields.Selection(
        related='parent_id.reporting_level',
        string='Reporting Level',
        readonly=True)
    computation_line_ids = fields.One2many(
        'intrastat.product.computation.line', 'declaration_line_id',
        string='Computation Lines', readonly=True)
    src_dest_country_id = fields.Many2one(
        'res.country', string='Country',
        help="Country of Origin/Destination",
        domain=[('intrastat', '=', True)])
    hs_code_id = fields.Many2one(
        'hs.code',
        string='Intrastat Code')
    intrastat_unit_id = fields.Many2one(
        'intrastat.unit', related='hs_code_id.intrastat_unit_id',
        string='Suppl. Unit', readonly=True,
        help="Intrastat Supplementary Unit")
    weight = fields.Integer(
        string='Weight (Kg)')
    suppl_unit_qty = fields.Integer(
        string='Suppl. Unit Qty',
        help="Supplementary Units Quantity")
    amount_company_currency = fields.Integer(
        string='Fiscal Value',
        help="Amount in company currency to write in the declaration. "
        "Amount in company currency = amount in invoice currency "
        "converted to company currency with the rate of the invoice date.")
    transaction_id = fields.Many2one(
        'intrastat.transaction',
        string='Intrastat Transaction')
    # extended declaration
    transport_id = fields.Many2one(
        'intrastat.transport_mode',
        string='Transport Mode')
