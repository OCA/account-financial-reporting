# -*- coding: utf-8 -*-
# Author: Andrea andrea4ever Gallina
# Author: Francesco OpenCode Apruzzese
# Author: Ciro CiroBoxHub Urselli
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api
from openerp.exceptions import Warning as UserError
from datetime import datetime


class OpenInvoiceWizard(models.TransientModel):

    _name = 'open.invoice.wizard'

    company_id = fields.Many2one(
        'res.company', required=True,
        default=lambda s: s.env.user.company_id)
    at_date = fields.Date(
        required=True,
        default=fields.Date.to_string(datetime.today()))
    partner_ids = fields.Many2many(
        'res.partner', string='Filter partners')
    result_selection = fields.Selection([
        ('customer', 'Receivable Accounts'),
        ('supplier', 'Payable Accounts'),
        ('customer_supplier', 'Receivable and Payable Accounts')],
        "Partner's", required=True, default='customer')
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')], 'Target Moves',
        required=True, default='all')

    @api.onchange('at_date')
    def onchange_atdate(self):
        self.until_date = self.at_date

    @api.onchange('until_date')
    def onchange_untildate(self):
        # ---- until_date must be always >= of at_date
        if self.until_date:
            if self.until_date < self.at_date:
                raise UserError(
                    'Until Date must be equal or greater than At Date')

    def _build_contexts(self, data):
        result = {}
        return result

    def _build_header(self):
        return {
            'company': self.company_id.name,
            'fiscal_year': '',
            'at_date': self.at_date,
            'account_filters': dict(
                self._columns['result_selection'].selection)[
                self.result_selection],
            'target_moves': dict(
                self._columns['target_move'].selection)[self.target_move],
        }

    def _get_form_fields(self):
        return self.read(['company_id', 'at_date', 'partner_ids',
                          'result_selection', 'target_move',
                          'until_date'])[0]

    @api.multi
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self._get_form_fields()
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(
            used_context, lang=self.env.context.get('lang', 'en_US'))
        data['header'] = self._build_header()
        return self.env['report'].get_action(
            self, 'account_financial_report_qweb.open_invoice_report_qweb',
            data=data)
