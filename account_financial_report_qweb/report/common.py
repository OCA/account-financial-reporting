# -*- encoding: utf-8 -*-
# © 2015 Yannick Vaucher
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api


class FinancialReportLine(models.AbstractModel):
    """Rappresentation of a report line."""

    _name = 'financial.report.line'
    _description = "Financial report line"

    _order = 'account_id, date'
    # TODO order by account_id.code

    name = fields.Char()
    ref = fields.Char()
    date = fields.Date()
    month = fields.Char()
    partner_name = fields.Char()
    partner_ref = fields.Char()
    account_id = fields.Many2one('account.account')
    account_code = fields.Char()
    journal_id = fields.Many2one('account.journal')

    currency_id = fields.Many2one('res.currency')
    currency_code = fields.Char()
    init_credit = fields.Float()
    init_debit = fields.Float()
    debit = fields.Float()
    credit = fields.Float()
    balance = fields.Float()
    amount_currency = fields.Float()

    cumul_credit = fields.Float()
    cumul_debit = fields.Float()
    cumul_balance = fields.Float()
    cumul_balance_curr = fields.Float()

    init_credit = fields.Float()
    init_debit = fields.Float()
    init_balance = fields.Float()
    init_balance_curr = fields.Float()

    debit_centralized = fields.Float()
    credit_centralized = fields.Float()
    balance_centralized = fields.Float()
    balance_curr_centralized = fields.Float()

    init_credit_centralized = fields.Float()
    init_debit_centralized = fields.Float()
    init_balance_centralized = fields.Float()
    init_balance_curr_centralized = fields.Float()

    move_name = fields.Char()
    move_state = fields.Char()
    invoice_number = fields.Char()

    centralized = fields.Boolean()


class CommonFinancialReport(models.AbstractModel):
    _name = 'account.report.common'

    start_date = fields.Date()
    end_date = fields.Date()

    fiscalyear = fields.Many2one('account.fiscalyear')

    centralize = fields.Boolean()
    target_move = fields.Char()

    filter = fields.Selection(
        [('filter_no', 'No Filters'),
         ('filter_date', 'Date'),
         ('filter_opening', 'Opening Only')],
        "Filter by",
        required=False,
        help='Filter by date: no opening balance will be displayed. '
             '(opening balance can only be computed based on period to be '
             'correct).'
    )

    @api.multi
    def _get_moves_from_dates_domain(self):
        """ Prepare domain for `_get_moves_from_dates` """
        domain = []
        if self.centralize:
            domain = [('centralized', '=', False)]
        start_date = self.start_date
        end_date = self.end_date
        if self.fiscalyear:
            start_date = self.fiscalyear.start_date
            end_date = self.fiscalyear.end_date
        if start_date:
            domain += [('date', '>=', start_date)]
        if end_date:
            domain += [('date', '<=', end_date)]

        if self.target_move == 'posted':
            domain += [('move_state', '=', 'posted')]

        if self.account_ids:
            domain += [('account_id', 'in', self.account_ids.ids)]

        domain += [('journal_id', 'in', self.journal_ids.ids)]
        return domain

    @api.multi
    def _get_moves_from_fiscalyear(self, account, fiscalyear,
                                   target_move):
        return self._get_moves_from_dates(
            account, fiscalyear.date_start, fiscalyear.date_end, target_move)
