# -*- coding: utf-8 -*-
# Author: Damien Crier
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from odoo import models, fields, api


class OpenItemsReportWizard(models.TransientModel):
    """Open items report wizard."""

    _name = "open.items.report.wizard"
    _description = "Open Items Report Wizard"

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )
    date_at = fields.Date(required=True,
                          default=fields.Date.to_string(datetime.today()))
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
    hide_account_balance_at_0 = fields.Boolean(
        string='Hide account ending balance at 0',
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
    )

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

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        return self._export()

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        return self._export(xlsx_report=True)

    def _prepare_report_open_items(self):
        self.ensure_one()
        return {
            'date_at': self.date_at,
            'only_posted_moves': self.target_move == 'posted',
            'hide_account_balance_at_0': self.hide_account_balance_at_0,
            'company_id': self.company_id.id,
            'filter_account_ids': [(6, 0, self.account_ids.ids)],
            'filter_partner_ids': [(6, 0, self.partner_ids.ids)],
        }

    def _export(self, xlsx_report=False):
        """Default export is PDF."""
        model = self.env['report_open_items_qweb']
        report = model.create(self._prepare_report_open_items())
        return report.print_report(xlsx_report)
