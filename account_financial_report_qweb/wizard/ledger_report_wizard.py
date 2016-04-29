# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api, _


class LedgerReportWizard(models.TransientModel):
    """Base ledger report wizard."""

    _name = "ledger.report.wizard"
    _description = "Ledger Report Wizard"

    company_id = fields.Many2one(comodel_name='res.company')
    date_range_id = fields.Many2one(comodel_name='date.range', required=True)
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    fy_start_date = fields.Date(required=True)
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
        [
            ('customer', 'Receivable Accounts'),
            ('supplier', 'Payable Accounts'),
            ('customer_supplier', 'Receivable and Payable Accounts'),
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
        """Execute query.

        Short summary:
        Prepare all lines for report
        by calculating debit/credit amounts
        plus the cumulative one.

        Narrow the search by using PG windows.

        Insert all the rows in `ledger_report_wizard_line`
        at once, so that we have real model objects
        and we can filter/group them in the tree view.

        """
        query = """
            WITH view_q as (SELECT
                ml.date,
                acc.id AS account_id,
                ml.debit,
                ml.credit,
                ml.name as name,
                ml.ref,
                ml.journal_id,
                ml.partner_id,
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
            WINDOW w_account AS (PARTITION BY acc.code ORDER BY ml.date, ml.id)
            ORDER BY acc.id, ml.date)
            INSERT INTO ledger_report_wizard_line (
                date,
                name,
                journal_id,
                account_id,
                partner_id,
                ref,
                label,
                --counterpart
                debit,
                credit,
                cumul_balance,
                wizard_id
            )
            SELECT
                date,
                name,
                journal_id,
                account_id,
                partner_id,
                ref,
                ' TODO label ' as label,
                --counterpart
                debit,
                credit,
                cumul_balance,
                %(wizard_id)s as wizard_id
            FROM view_q
            WHERE date BETWEEN %(date_from)s AND %(date_to)s
            """

        params = dict(fy_date=self.fy_start_date, wizard_id=self.id,
                      date_from=self.date_from, date_to=self.date_to)
        self.env.cr.execute(query, params)
        return True

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
        """Open tree view w/ results."""
        return self.process()

    @api.multi
    def process(self):
        """Process data and return window action."""
        self._query()

        return {
            'domain': [('wizard_id', '=', self.id)],
            'name': _('Ledger lines'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'ledger.report.wizard.line',
            'view_id': False,
            'context': {
                'search_default_group_by_account_id': True,
                'search_default_group_by_date': True,
            },
            'type': 'ir.actions.act_window'
        }

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end
        if self.date_from:
            self.fy_start_date = self.date_range_id.find_daterange_fy_start(
                fields.Date.from_string(self.date_range_id.date_start))


class LedgerReportWizardLine(models.TransientModel):
    """A wizard line.

    Lines are populated on the fly when submitting the wizard.
    """
    _name = 'ledger.report.wizard.line'

    wizard_id = fields.Many2one(comodel_name='ledger.report.wizard')

    name = fields.Char()
    label = fields.Char()
    ref = fields.Char()
    date = fields.Date()
    month = fields.Char()
    partner_name = fields.Char()
    partner_ref = fields.Char()
    account_id = fields.Many2one('account.account')
    account_code = fields.Char()
    journal_id = fields.Many2one('account.journal')
    partner_id = fields.Many2one('res.partner')

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
