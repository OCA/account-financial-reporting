# -*- coding: utf-8 -*-
# Author: Guewen Baconnier, Leonardo Pistone
# © 2011-2016 Camptocamp

from openerp import fields, models, api


class AccountPartnerBalanceWizard(models.TransientModel):

    """Will launch partner balance report and pass required args"""

    # pylint: disable=consider-merging-classes-inherited
    _inherit = "account.common.balance.report"
    _name = "partner.balance.webkit"
    _description = "Partner Balance Report"

    result_selection = fields.Selection(
        [
            ('customer', 'Receivable Accounts'),
            ('supplier', 'Payable Accounts'),
            ('customer_supplier', 'Receivable and Payable Accounts')
        ],
        "Partner's", required=True, default='customer_supplier')
    partner_ids = fields.Many2many(
        'res.partner', string='Filter on partner',
        help="Only selected partners will be printed. "
        "Leave empty to print all partners.")

    # same field in the module account
    display_partner = fields.Selection(
        [
            ('non-zero_balance', 'With non-zero balance'),
            ('all', 'All Partners')
        ], 'Display Partners', default='all')

    @api.multi
    def pre_print_report(self, data):
        self.ensure_one()

        data = super(AccountPartnerBalanceWizard, self).pre_print_report(data)
        vals = self.read(['result_selection', 'partner_ids',
                          'display_partner'])[0]
        data['form'].update(vals)
        return data

    @api.multi
    def _print_report(self, data):
        # we update form with display account value
        data = self.pre_print_report(data)

        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.account_report_partner_balance_webkit',
                'datas': data}
