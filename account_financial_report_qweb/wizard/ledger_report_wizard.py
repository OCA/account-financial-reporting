# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api


class LedgerReportWizard(models.TransientModel):

    _name = "ledger.report.wizard"
    _description = "Ledger Report Wizard"

    company_id = fields.Many2one(comodel_name='res.company')
    # date_range = ??
    date_from = fields.Date()
    date_to = fields.Date()
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')],
                                   string='Target Moves',
                                   required=True,
                                   default='posted')
    account_ids = fields.Many2many(
        comodel_name='account.account',
        string='Filter accounts',
    )
    amount_currency = fields.Boolean(string='With currency',
                                     default=False)
    centralize = fields.Boolean(string='Activate centralization',
                                default=False)
    result_selection = fields.Selection(
        [('customer', 'Receivable Accounts'),
         ('supplier', 'Payable Accounts'),
         ('customer_supplier', 'Receivable and Payable Accounts')
         ],
        string="Partner's",
        default='customer')
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Filter partners',
    )

    @api.multi
    def pre_print_report(self, data):
        data = {'form': {}}

        # will be used to attach the report on the main account
        vals = self.read(['amount_currency',
                          'account_ids',
                          'journal_ids',
                          'centralize',
                          'target_move',
                          'date_from',
                          'date_to',
                          'fiscalyear'])[0]
        data['form'].update(vals)
        return data

    @api.multi
    def _print_report(self, data):
        # we update form with display account value
        data = self.pre_print_report(data)
        Report = self.env['report'].with_context(landscape=True)
        return Report.get_action(
            self, 'account.report_generalledger_qweb',
            data=data)

    def _build_contexts(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        return result

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        return self._print_report(data)
