# Author: Damien Crier
# Author: Julien Coux
# Author: Jordi Ballester
# Copyright 2016 Camptocamp SA
# Copyright 2017 Akretion - Alexis de Lattre
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# Copyright 2020 Druidoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat
from odoo.exceptions import ValidationError
import time


class GeneralLedgerReportWizard(models.TransientModel):
    """General ledger report wizard."""

    _name = "general.ledger.report.wizard"
    _description = "General Ledger Report Wizard"
    _inherit = 'account_financial_report_abstract_wizard'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        required=False,
        string='Company'
    )
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date range'
    )
    date_from = fields.Date(required=True,
                            default=lambda self: self._init_date_from())
    date_to = fields.Date(required=True,
                          default=fields.Date.context_today)
    fy_start_date = fields.Date(compute='_compute_fy_start_date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')],
                                   string='Target Moves',
                                   required=True,
                                   default='all')
    account_ids = fields.Many2many(
        comodel_name='account.account',
        string='Filter accounts',
    )
    centralize = fields.Boolean(string='Activate centralization',
                                default=True)
    hide_account_at_0 = fields.Boolean(
        string='Hide account ending balance at 0',
        help='Use this filter to hide an account or a partner '
             'with an ending balance at 0. '
             'If partners are filtered, '
             'debits and credits totals will not match the trial balance.'
    )
    show_analytic_tags = fields.Boolean(
        string='Show analytic tags',
    )
    account_type_ids = fields.Many2many(
        'account.account.type',
        string='Account Types',
    )
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Filter partners',
        default=lambda self: self._default_partners(),
    )
    analytic_tag_ids = fields.Many2many(
        comodel_name='account.analytic.tag',
        string='Filter analytic tags',
    )
    account_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string='Filter journals',
    )
    cost_center_ids = fields.Many2many(
        comodel_name='account.analytic.account',
        string='Filter cost centers',
    )

    not_only_one_unaffected_earnings_account = fields.Boolean(
        readonly=True,
        string='Not only one unaffected earnings account'
    )
    foreign_currency = fields.Boolean(
        string='Show foreign currency',
        help='Display foreign currency for move lines, unless '
             'account currency is not setup through chart of accounts '
             'will display initial and final balance in that currency.',
        default=lambda self: self._default_foreign_currency(),
    )
    partner_ungrouped = fields.Boolean(
        string='Partner ungrouped',
        help='If set moves are not grouped by partner in any case'
    )

    def _init_date_from(self):
        """set start date to begin of current year if fiscal year running"""
        today = fields.Date.context_today(self)
        cur_month = fields.Date.from_string(today).month
        cur_day = fields.Date.from_string(today).day
        last_fsc_month = self.env.user.company_id.fiscalyear_last_month
        last_fsc_day = self.env.user.company_id.fiscalyear_last_day

        if cur_month < last_fsc_month \
                or cur_month == last_fsc_month and cur_day <= last_fsc_day:
            return time.strftime('%Y-01-01')

    def _default_foreign_currency(self):
        return self.env.user.has_group('base.group_multi_currency')

    @api.depends('date_from')
    def _compute_fy_start_date(self):
        for wiz in self.filtered('date_from'):
            date = fields.Datetime.from_string(wiz.date_from)
            res = self.company_id.compute_fiscalyear_dates(date)
            wiz.fy_start_date = fields.Date.to_string(res['date_from'])

    @api.onchange('company_id')
    def onchange_company_id(self):
        """Handle company change."""
        account_type = self.env.ref('account.data_unaffected_earnings')
        count = self.env['account.account'].search_count(
            [
                ('user_type_id', '=', account_type.id),
                ('company_id', '=', self.company_id.id)
            ])
        self.not_only_one_unaffected_earnings_account = count != 1
        if self.company_id and self.date_range_id.company_id and \
                self.date_range_id.company_id != self.company_id:
            self.date_range_id = False
        if self.company_id and self.account_journal_ids:
            self.account_journal_ids = self.account_journal_ids.filtered(
                lambda p: p.company_id == self.company_id or
                not p.company_id)
        if self.company_id and self.partner_ids:
            self.partner_ids = self.partner_ids.filtered(
                lambda p: p.company_id == self.company_id or
                not p.company_id)
        if self.company_id and self.account_ids:
            if self.account_type_ids:
                self._onchange_account_type_ids()
            else:
                self.account_ids = self.account_ids.filtered(
                    lambda a: a.company_id == self.company_id)
        if self.company_id and self.cost_center_ids:
            self.cost_center_ids = self.cost_center_ids.filtered(
                lambda c: c.company_id == self.company_id)
        res = {'domain': {'account_ids': [],
                          'partner_ids': [],
                          'account_journal_ids': [],
                          'cost_center_ids': [],
                          'date_range_id': []
                          }
               }
        if not self.company_id:
            return res
        else:
            res['domain']['account_ids'] += [
                ('company_id', '=', self.company_id.id)]
            res['domain']['account_journal_ids'] += [
                ('company_id', '=', self.company_id.id)]
            res['domain']['partner_ids'] += self._get_partner_ids_domain()
            res['domain']['cost_center_ids'] += [
                ('company_id', '=', self.company_id.id)]
            res['domain']['date_range_id'] += [
                '|', ('company_id', '=', self.company_id.id),
                ('company_id', '=', False)]
        return res

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    @api.multi
    @api.constrains('company_id', 'date_range_id')
    def _check_company_id_date_range_id(self):
        for rec in self.sudo():
            if rec.company_id and rec.date_range_id.company_id and\
                    rec.company_id != rec.date_range_id.company_id:
                raise ValidationError(
                    _('The Company in the General Ledger Report Wizard and in '
                      'Date Range must be the same.'))

    @api.onchange('account_type_ids')
    def _onchange_account_type_ids(self):
        if self.account_type_ids:
            self.account_ids = self.env['account.account'].search([
                ('company_id', '=', self.company_id.id),
                ('user_type_id', 'in', self.account_type_ids.ids)])
        else:
            self.account_ids = None

    @api.onchange('partner_ids')
    def onchange_partner_ids(self):
        """Handle partners change."""
        if self.partner_ids:
            self.account_type_ids = self.env['account.account.type'].search([
                ('type', 'in', ['receivable', 'payable'])])
        else:
            self.account_type_ids = None
        # Somehow this is required to force onchange on _default_partners()
        self._onchange_account_type_ids()

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'account_financial_report.action_report_general_ledger')
        action_data = action.read()[0]
        context1 = action_data.get('context', {})
        if isinstance(context1, pycompat.string_types):
            context1 = safe_eval(context1)
        model = self.env['report_general_ledger']
        report = model.create(self._prepare_report_general_ledger())
        report.compute_data_for_report()
        context1['active_id'] = report.id
        context1['active_ids'] = report.ids
        action_data['context'] = context1
        return action_data

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export(report_type)

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = 'xlsx'
        return self._export(report_type)

    def _prepare_report_general_ledger(self):
        self.ensure_one()
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'only_posted_moves': self.target_move == 'posted',
            'hide_account_at_0': self.hide_account_at_0,
            'foreign_currency': self.foreign_currency,
            'show_analytic_tags': self.show_analytic_tags,
            'company_id': self.company_id.id,
            'filter_account_ids': [(6, 0, self.account_ids.ids)],
            'filter_partner_ids': [(6, 0, self.partner_ids.ids)],
            'filter_cost_center_ids': [(6, 0, self.cost_center_ids.ids)],
            'filter_analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'filter_journal_ids': [(6, 0, self.account_journal_ids.ids)],
            'centralize': self.centralize,
            'fy_start_date': self.fy_start_date,
            'partner_ungrouped': self.partner_ungrouped,
        }

    def _export(self, report_type):
        """Default export is PDF."""
        model = self.env['report_general_ledger']
        report = model.create(self._prepare_report_general_ledger())
        report.compute_data_for_report()
        return report.print_report(report_type)
