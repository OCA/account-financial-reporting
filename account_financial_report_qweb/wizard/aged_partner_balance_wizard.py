# -*- coding: utf-8 -*-
# Author: Damien Crier, Andrea Stirpe, Kevin Graveman, Dennis Sluijk
# Author: Julien Coux
# Copyright 2016 Camptocamp SA, Onestein B.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class AgedPartnerBalance(models.TransientModel):
    """Aged partner balance report wizard."""

    _name = 'aged.partner.balance.wizard'
    _description = 'Aged Partner Balance Wizard'

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
    )
    receivable_accounts_only = fields.Boolean()
    payable_accounts_only = fields.Boolean()
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Filter partners',
    )
    show_move_line_details = fields.Boolean()

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

    @api.model
    def create(self, vals):
        """
        This is a workaround for bug https://github.com/odoo/odoo/issues/14761
        This bug impacts M2M fields in wizards filled-up via onchange
        It replaces the workaround widget="many2many_tags" on
        field name="account_ids" which prevented from selecting several
        accounts at the same time (quite useful when you want to select
        an interval of accounts for example)
        """
        if 'account_ids' in vals and isinstance(vals['account_ids'], list):
            account_ids = []
            for account in vals['account_ids']:
                if account[0] in (1, 4):
                    account_ids.append(account[1])
                elif account[0] == 6 and isinstance(account[2], list):
                    account_ids += account[2]
            vals['account_ids'] = [(6, 0, account_ids)]
        res = super(AgedPartnerBalance, self).create(vals)
        return res

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'account_financial_report_qweb.action_report_aged_partner_balance')
        vals = action.read()[0]
        context1 = vals.get('context', {})
        if isinstance(context1, basestring):
            context1 = safe_eval(context1)
        model = self.env['report_aged_partner_balance_qweb']
        report = model.create(self._prepare_report_aged_partner_balance())
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

    def _prepare_report_aged_partner_balance(self):
        self.ensure_one()
        return {
            'date_at': self.date_at,
            'only_posted_moves': self.target_move == 'posted',
            'company_id': self.company_id.id,
            'filter_account_ids': [(6, 0, self.account_ids.ids)],
            'filter_partner_ids': [(6, 0, self.partner_ids.ids)],
            'show_move_line_details': self.show_move_line_details,
        }

    def _export(self, report_type):
        """Default export is PDF."""
        model = self.env['report_aged_partner_balance_qweb']
        report = model.create(self._prepare_report_aged_partner_balance())
        report.compute_data_for_report()
        return report.print_report(report_type)
