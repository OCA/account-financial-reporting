# -*- coding: utf-8 -*-
# Author: Andrea andrea4ever Gallina
# Author: Francesco OpenCode Apruzzese
# Author: Ciro CiroBoxHub Urselli
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _
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
    amount_currency = fields.Boolean(
        "With Currency", help="It adds the currency column")
    group_by_currency = fields.Boolean(
        "Group Partner by currency", help="It adds the currency column")
    result_selection = fields.Selection([
        ('customer', 'Receivable Accounts'),
        ('supplier', 'Payable Accounts'),
        ('customer_supplier', 'Receivable and Payable Accounts')],
        "Partner's", required=True, default='customer')
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')], 'Target Moves',
        required=True, default='all')
    until_date = fields.Date(
        "Clearance date", required=True,
        help="""The clearance date is essentially a tool used for debtors
        provisionning calculation.
        By default, this date is equal to the the end date (
        ie: 31/12/2011 if you select fy 2011).
        By amending the clearance date, you will be, for instance,
        able to answer the question : 'based on my last
        year end debtors open invoices, which invoices are still
        unpaid today (today is my clearance date)?'""")

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

    @staticmethod
    def _get_domain(data):
        account_type = ('payable', 'receivable')
        if data['result_selection'] == 'customer':
            account_type = ('receivable', )
        elif data['result_selection'] == 'supplier':
            account_type = ('payable', )
        domain = [
            ('company_id', '=', data['company_id'].id),
            ('move_id.date', '>=', data['at_date']),
            ('move_id.date', '<=', data['until_date']),
            ('account_id.user_type_id.type', 'in', account_type)
            ]
        if data['target_move'] != 'all':
            domain.append(('move_id.state', 'in', ('posted', )), )
        if data['partner_ids']:
            domain.append(('partner_id', 'in', [p.id
                                                for p
                                                in data['partner_ids']]), )
        return domain

    @staticmethod
    def _get_moves_data(move):
        # return {
        #     'date': data.date,
        #     'period': data.invoice_id.period_id.name,
        #     'journal': data.move_id.journal_id.name,
        #     'reference': data.,
        #     '': data.,
        #     '': data.,
        #     }
        return {
            'date': '',
            'period': '',
            'entry': '',
            'journal': '',
            'reference': '',
            'label': '',
            'rec': '',
            'due_date': '',
            'debit': '',
            'credit': '',
            'balance': '',
            }

    @api.multi
    def print_report(self):
        self.ensure_one()
        moves = self.env['account.move.line'].search(self._get_domain(self))
        if not moves:
            return True  # ----- Show a message here
        datas = {}
        for move in moves:
            if move.account_id.name not in datas:
                datas[move.account_id.name] = {}
            if move.partner_id.name not in datas[move.account_id.name]:
                datas[move.account_id.name][move.partner_id.name] = []
            datas[move.account_id.name][move.partner_id.name].append(
                self._get_moves_data(move))
        return self.env['report'].get_action(
            self, 'account_financial_report_qweb.open_invoice_report_qweb',
            data={'data': datas})

