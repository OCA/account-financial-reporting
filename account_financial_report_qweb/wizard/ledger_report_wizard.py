# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api, _


class LedgerReportWizard(models.TransientModel):

    _name = "ledger.report.wizard"
    _description = "Ledger Report Wizard"

    company_id = fields.Many2one(comodel_name='res.company')
    date_range_id = fields.Many2one(comodel_name='date.range', required=True)
    date_from = fields.Date()
    date_to = fields.Date()
    fy_start_date = fields.Date(default='2016-01-01')
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
    line_ids = fields.One2many(comodel_name='ledger.report.wizard.line',
                               inverse_name='wizard_id')

    def _query(self):
        query = """
              WITH view_q as (SELECT
                ml.date,
                acc.id AS account_id,
                ml.debit,
                ml.credit,
                SUM(debit) OVER w_account - debit AS init_debit,
                SUM(credit) OVER w_account - credit AS init_credit,
                SUM(debit - credit) OVER w_account - (debit - credit)
                    AS init_balance,
                SUM(debit - credit) OVER w_account AS cumul_balance
              FROM
                account_account AS acc
                LEFT JOIN account_move_line AS ml ON (ml.account_id = acc.id)
                --INNER JOIN res_partner AS part ON (ml.partner_id = part.id)
              INNER JOIN account_move AS m ON (ml.move_id = m.id)
              WINDOW w_account AS (
                  PARTITION BY acc.code ORDER BY ml.date, ml.id)
              ORDER BY acc.id, ml.date)
              SELECT * from view_q where date >= %s
            """

        params = (self.fy_start_date,)
        self.env.cr.execute(query, params)

        return self.env.cr.fetchall()

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
        result['journal_ids'] = (
            'journal_ids' in data['form'] and
            data['form']['journal_ids'] or False
        )
        result['state'] = (
            'target_move' in data['form'] and
            data['form']['target_move'] or ''
        )
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        return result

    @api.multi
    def button_view(self):
        return self.process()

    @api.multi
    def process(self):
        ledger_line_obj = self.env['ledger.report.wizard.line']
        rows = self._query()
        res = []
        for row in rows:
            data = {
                'wizard_id': self.id,
                'date': row[0],
                'account_id': row[1],
                'debit': row[2],
                'credit': row[3],
                'init_debit': row[4],
                'init_credit': row[5],
                'init_balance': row[6],
                'cumul_balance': row[7]
            }
            gll = ledger_line_obj.create(data)
            res.append(gll.id)

        return {
            'domain': [('wizard_id', '=', self.id)],
            'name': _('Ledger lines'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'ledger.report.wizard.line',
            'view_id': False,
            'context': False,
            'type': 'ir.actions.act_window'
        }

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end


class LedgerReportWizardLine(models.TransientModel):
    _name = 'ledger.report.wizard.line'

    wizard_id = fields.Many2one(comodel_name='ledger.report.wizard')

    name = fields.Char()
    ref = fields.Char()
    date = fields.Date()
    month = fields.Char()
    partner_name = fields.Char()
    partner_ref = fields.Char()
    account_id = fields.Many2one('account.account')
    account_code = fields.Char()
    journal_id = fields.Many2one('account.journal')

    init_credit = fields.Float()
    init_debit = fields.Float()
    debit = fields.Float()
    credit = fields.Float()
    balance = fields.Float()

    cumul_credit = fields.Float()
    cumul_debit = fields.Float()
    cumul_balance = fields.Float()

    init_credit = fields.Float()
    init_debit = fields.Float()
    init_balance = fields.Float()

    move_name = fields.Char()
    move_state = fields.Char()
    invoice_number = fields.Char()

    centralized = fields.Boolean()
