# Author: Damien Crier
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat


class OpenItemsReportWizard(models.TransientModel):
    """Open items report wizard."""

    _name = "open.items.report.wizard"
    _description = "Open Items Report Wizard"
    _inherit = 'account_financial_report_abstract_wizard'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        required=False,
        string='Company'
    )
    date_at = fields.Date(required=True,
                          default=fields.Date.context_today)
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')],
                                   string='Target Moves',
                                   required=True,
                                   default='all')
    account_ids = fields.Many2many(
        comodel_name='account.account',
        string='Filter accounts',
        domain=[('reconcile', '=', True)],
    )
    hide_account_at_0 = fields.Boolean(
        string='Hide account ending balance at 0', default=True,
        help='Use this filter to hide an account or a partner '
             'with an ending balance at 0. '
             'If partners are filtered, '
             'debits and credits totals will not match the trial balance.'
    )
    receivable_accounts_only = fields.Boolean()
    payable_accounts_only = fields.Boolean()
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Filter partners',
        default=lambda self: self._default_partners(),
    )
    foreign_currency = fields.Boolean(
        string='Show foreign currency',
        help='Display foreign currency for move lines, unless '
             'account currency is not setup through chart of accounts '
             'will display initial and final balance in that currency.',
        default=lambda self: self._default_foreign_currency(),
    )

    def _default_foreign_currency(self):
        return self.env.user.has_group('base.group_multi_currency')

    @api.onchange('company_id')
    def onchange_company_id(self):
        """Handle company change."""
        if self.company_id and self.partner_ids:
            self.partner_ids = self.partner_ids.filtered(
                lambda p: p.company_id == self.company_id or
                not p.company_id)
        if self.company_id and self.account_ids:
            if self.receivable_accounts_only or self.payable_accounts_only:
                self.onchange_type_accounts_only()
            else:
                self.account_ids = self.account_ids.filtered(
                    lambda a: a.company_id == self.company_id)
        res = {'domain': {'account_ids': [],
                          'partner_ids': []}}
        if not self.company_id:
            return res
        else:
            res['domain']['account_ids'] += [
                ('company_id', '=', self.company_id.id)]
            res['domain']['partner_ids'] += self._get_partner_ids_domain()
        return res

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

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'account_financial_report.action_report_open_items')
        vals = action.read()[0]
        context1 = vals.get('context', {})
        if isinstance(context1, pycompat.string_types):
            context1 = safe_eval(context1)
        model = self.env['report_open_items']
        report = model.create(self._prepare_report_open_items())
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

    def _prepare_report_open_items(self):
        self.ensure_one()
        return {
            'date_at': self.date_at,
            'only_posted_moves': self.target_move == 'posted',
            'hide_account_at_0': self.hide_account_at_0,
            'foreign_currency': self.foreign_currency,
            'company_id': self.company_id.id,
            'filter_account_ids': [(6, 0, self.account_ids.ids)],
            'filter_partner_ids': [(6, 0, self.partner_ids.ids)],
        }

    def _export(self, report_type):
        """Default export is PDF."""
        model = self.env['report_open_items']
        report = model.create(self._prepare_report_open_items())
        report.compute_data_for_report()
        return report.print_report(report_type)
