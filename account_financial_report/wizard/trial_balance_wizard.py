# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# Copyright 2017 Akretion - Alexis de Lattre
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat


class TrialBalanceReportWizard(models.TransientModel):
    """Trial balance report wizard."""

    _name = "trial.balance.report.wizard"
    _description = "Trial Balance Report Wizard"

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
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
    hierarchy_on = fields.Selection([('computed', 'Computed Accounts'),
                                     ('relation', 'Child Accounts')],
                                    string='Hierarchy On',
                                    required=True,
                                    default='computed')
    account_ids = fields.Many2many(
        comodel_name='account.account',
        string='Filter accounts',
    )
    hide_account_balance_at_0 = fields.Boolean(
        string='Hide account ending balance at 0',
        help='Use this filter to hide an account or a partner '
             'with an ending balance at 0. '
             'If partners are filtered, '
             'debits and credits totals will not match the trial balance.'
    )
    receivable_accounts_only = fields.Boolean()
    payable_accounts_only = fields.Boolean()
    show_partner_details = fields.Boolean()
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Filter partners',
    )

    not_only_one_unaffected_earnings_account = fields.Boolean(
        readonly=True,
        string='Not only one unaffected earnings account'
    )

    @api.depends('date_from')
    def _compute_fy_start_date(self):
        for wiz in self.filtered('date_from'):
            date = fields.Datetime.from_string(wiz.date_from)
            res = self.company_id.compute_fiscalyear_dates(date)
            wiz.fy_start_date = res['date_from']

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

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    @api.onchange('receivable_accounts_only', 'payable_accounts_only')
    def onchange_type_accounts_only(self):
        """Handle receivable/payable accounts only change."""
        if self.receivable_accounts_only or self.payable_accounts_only:
            domain = []
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
            self.hide_account_balance_at_0 = True
        else:
            self.receivable_accounts_only = self.payable_accounts_only = False
            self.hide_account_balance_at_0 = False

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
            'hide_account_balance_at_0': self.hide_account_balance_at_0,
            'company_id': self.company_id.id,
            'filter_account_ids': [(6, 0, self.account_ids.ids)],
            'filter_partner_ids': [(6, 0, self.partner_ids.ids)],
            'fy_start_date': self.fy_start_date,
            'hierarchy_on': self.hierarchy_on,
            'show_partner_details': self.show_partner_details,
        }

    def _export(self, report_type):
        """Default export is PDF."""
        model = self.env['report_trial_balance']
        report = model.create(self._prepare_report_trial_balance())
        report.compute_data_for_report()
        return report.print_report(report_type)
