# -*- coding: utf-8 -*-
# Author: Thomas Rehn, Guewen Baconnier
# Copyright 2016 initOS GmbH, camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class AccountBalanceCommonWizard(models.TransientModel):
    """Will launch some balance report wizards and pass required args"""

    _inherit = "account.common.account.report"
    _name = "account.common.balance.report"
    _description = "Common Balance Report"

    @api.model
    def _get_account_ids(self):
        context = self.env.context or {}
        res = False
        if context.get('active_model', False) == 'account.account' \
                and context.get('active_ids', False):
            res = context['active_ids']
        return res

    account_ids = fields.Many2many(
        comodel_name='account.account',
        string='Filter on accounts',
        help="Only selected accounts will be printed. Leave empty to "
             "print all accounts.",
        default=_get_account_ids
    )
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date Range',
    )
    comparison_date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date Range',
    )
    comparison_date_start = fields.Datetime(
        string='Start Date'
    )
    comparison_date_end = fields.Datetime(
        string='End Date'
    )
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Filter on partner',
        help="Only selected partners will be printed. "
             "Leave empty to print all partners."
    )
    debit_credit = fields.Boolean(
        string='Display Debit/Credit Columns',
        help="This option allows you to get more details about the way your "
             "balances are computed. Because it is space consuming, "
             "we do not allow to use it while doing a comparison."
    )

    def pre_print_report(self, cr, uid, ids, data, context=None):
        data = super(AccountBalanceCommonWizard, self).pre_print_report(
            cr, uid, ids, data, context)
        return data
