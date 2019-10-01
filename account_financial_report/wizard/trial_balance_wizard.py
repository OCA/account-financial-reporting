# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# Copyright 2017 Akretion - Alexis de Lattre
# Copyright 2018 Eficent Business and IT Consuting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat
from odoo.exceptions import UserError, ValidationError


class TrialBalanceReportWizard(models.TransientModel):
    """Trial balance report wizard."""

    _name = "trial.balance.report.wizard"
    _description = "Trial Balance Report Wizard"
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
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    fy_start_date = fields.Date(compute='_compute_fy_start_date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')],
                                   string='Target Moves',
                                   required=True,
                                   default='all')
    hierarchy_on = fields.Selection(
        [('computed', 'Computed Accounts'),
         ('relation', 'Child Accounts'),
         ('none', 'No hierarchy')],
        string='Hierarchy On',
        required=True,
        default='computed',
        help="""Computed Accounts: Use when the account group have codes
        that represent prefixes of the actual accounts.\n
        Child Accounts: Use when your account groups are hierarchical.\n
        No hierarchy: Use to display just the accounts, without any grouping.
        """,
    )
    limit_hierarchy_level = fields.Boolean('Limit hierarchy levels')
    show_hierarchy_level = fields.Integer('Hierarchy Levels to display',
                                          default=1)
    hide_parent_hierarchy_level = fields.Boolean(
        'Do not display parent levels', default=False)
    account_ids = fields.Many2many(
        comodel_name='account.account',
        string='Filter accounts',
    )
    hide_account_at_0 = fields.Boolean(
        string='Hide accounts at 0', default=True,
        help='When this option is enabled, the trial balance will '
             'not display accounts that have initial balance = '
             'debit = credit = end balance = 0',
    )
    receivable_accounts_only = fields.Boolean()
    payable_accounts_only = fields.Boolean()
    show_partner_details = fields.Boolean()
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Filter partners',
    )
    journal_ids = fields.Many2many(
        comodel_name="account.journal",
    )

    not_only_one_unaffected_earnings_account = fields.Boolean(
        readonly=True,
        string='Not only one unaffected earnings account'
    )

    foreign_currency = fields.Boolean(
        string='Show foreign currency',
        help='Display foreign currency for move lines, unless '
             'account currency is not setup through chart of accounts '
             'will display initial and final balance in that currency.'
    )

    @api.multi
    @api.constrains('hierarchy_on', 'show_hierarchy_level')
    def _check_show_hierarchy_level(self):
        for rec in self:
            if rec.hierarchy_on != 'none' and rec.show_hierarchy_level <= 0:
                raise UserError(_('The hierarchy level to filter on must be '
                                  'greater than 0.'))

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
        if self.company_id and self.partner_ids:
            self.partner_ids = self.partner_ids.filtered(
                lambda p: p.company_id == self.company_id or
                not p.company_id)
        if self.company_id and self.journal_ids:
            self.journal_ids = self.journal_ids.filtered(
                lambda a: a.company_id == self.company_id)
        if self.company_id and self.account_ids:
            if self.receivable_accounts_only or self.payable_accounts_only:
                self.onchange_type_accounts_only()
            else:
                self.account_ids = self.account_ids.filtered(
                    lambda a: a.company_id == self.company_id)
        res = {'domain': {'account_ids': [],
                          'partner_ids': [],
                          'date_range_id': [],
                          'journal_ids': [],
                          }
               }
        if not self.company_id:
            return res
        else:
            res['domain']['account_ids'] += [
                ('company_id', '=', self.company_id.id)]
            res['domain']['partner_ids'] += self._get_partner_ids_domain()
            res['domain']['date_range_id'] += [
                '|', ('company_id', '=', self.company_id.id),
                ('company_id', '=', False)]
            res['domain']['journal_ids'] += [
                ('company_id', '=', self.company_id.id)]
        return res

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    @api.multi
    @api.constrains('company_id', 'date_range_id')
    def _check_company_id_date_range_id(self):
        for rec in self.sudo():
            if rec.company_id and rec.date_range_id.company_id and\
                    rec.company_id != rec.date_range_id.company_id:
                raise ValidationError(
                    _('The Company in the Trial Balance Report Wizard and in '
                      'Date Range must be the same.'))

    @api.onchange('receivable_accounts_only', 'payable_accounts_only')
    def onchange_type_accounts_only(self):
        """Handle receivable/payable accounts only change."""
        if self.receivable_accounts_only or self.payable_accounts_only:
            domain = [('company_id', '=', self.company_id.id)]
            if self.receivable_accounts_only and self.payable_accounts_only:
                domain += [('internal_type', 'in', ('receivable', 'payable'))]
            elif self.receivable_accounts_only:
                domain += [('internal_type', '=', 'receivable')]
            elif self.payable_accounts_only:
                domain += [('internal_type', '=', 'payable')]
            self.account_ids = self.env['account.account'].search(domain)
        else:
            self.account_ids = None

    @api.onchange('show_partner_details')
    def onchange_show_partner_details(self):
        """Handle partners change."""
        if self.show_partner_details:
            self.receivable_accounts_only = self.payable_accounts_only = True
        else:
            self.receivable_accounts_only = self.payable_accounts_only = False

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'account_financial_report.action_report_trial_balance')
        vals = action.read()[0]
        context1 = vals.get('context', {})
        if isinstance(context1, pycompat.string_types):
            context1 = safe_eval(context1)
        model = self.env['report_trial_balance']
        report = model.create(self._prepare_report_trial_balance())
        report.compute_data_for_report()

        context1['active_id'] = report.id
        context1['active_ids'] = report.ids
        vals['context'] = context1
        return vals

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

    def _prepare_report_trial_balance(self):
        self.ensure_one()
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'only_posted_moves': self.target_move == 'posted',
            'hide_account_at_0': self.hide_account_at_0,
            'foreign_currency': self.foreign_currency,
            'company_id': self.company_id.id,
            'filter_account_ids': [(6, 0, self.account_ids.ids)],
            'filter_partner_ids': [(6, 0, self.partner_ids.ids)],
            'filter_journal_ids': [(6, 0, self.journal_ids.ids)],
            'fy_start_date': self.fy_start_date,
            'hierarchy_on': self.hierarchy_on,
            'limit_hierarchy_level': self.limit_hierarchy_level,
            'show_hierarchy_level': self.show_hierarchy_level,
            'hide_parent_hierarchy_level': self.hide_parent_hierarchy_level,
            'show_partner_details': self.show_partner_details,
        }

    def _export(self, report_type):
        """Default export is PDF."""
        model = self.env['report_trial_balance']
        report = model.create(self._prepare_report_trial_balance())
        report.compute_data_for_report()
        return report.print_report(report_type)
