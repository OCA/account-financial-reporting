# -*- coding: utf-8 -*-
# © 2011 Nicolas Bessi, Guewen Baconnier (Camptocamp)
# © 2015 Yannick Vaucher (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).-
import time

from openerp import models, fields, api


class FinancialReportGeneralLedgerWizard(models.TransientModel):

    """Will launch general ledger report and pass required args"""

    _inherit = "account.common.account.report"
    _name = "financial.report.general.ledger"
    _description = "General Ledger Report"

    @api.multi
    def _get_account_ids(self):
        res = False
        context = self.env.context
        if (context.get('active_model') == 'account.account' and
                context.get('active_ids')):
            res = context['active_ids']
        return res

    fiscalyear = fields.Many2one(
        'account.fiscalyear',
    )

    date_from_fy = fields.Date(
        related='fiscalyear.start_date',
        readonly=True
    )
    date_to_fy = fields.Date(
        related='fiscalyear.end_date',
        readonly=True
    )

    account_ids = fields.Many2many(
        'account.account',
        string='Filter on accounts',
        default=_get_account_ids,
        help="Only selected accounts will be printed. Leave empty to "
             "print all accounts."
    )
    centralize = fields.Boolean(
        'Activate Centralization',
        default=True,
        help='Uncheck to display all the details of centralized accounts.'
    )

    display_initial_balance = fields.Boolean()

    def _check_fiscalyear(self, cr, uid, ids, context=None):
        obj = self.read(
            cr, uid, ids[0], ['fiscalyear', 'filter'], context=context)
        if not obj['fiscalyear'] and obj['filter'] == 'filter_no':
            return False
        return True

    _constraints = [
        (_check_fiscalyear,
         'When no Fiscal year is selected, you must choose to filter by date.',
         ['filter']),
    ]

    @api.multi
    def pre_print_report(self, data):
        data = super(FinancialReportGeneralLedgerWizard, self
                     ).pre_print_report(data)
        # will be used to attach the report on the main account
        vals = self.read(['amount_currency',
                          'account_ids',
                          'journal_ids',
                          'centralize',
                          'target_move',
                          'date_from',
                          'date_to',
                          'fiscalyear'])[0]
        data['form'].update(vals)
        return data

    @api.onchange('filter')
    def onchange_filter(self, cr, uid, ids, filter='filter_no',
                        fiscalyear_id=False, context=None):
        res = {}
        if filter == 'filter_no':
            res['value'] = {
                'date_from': False,
                'date_to': False,
            }
        if filter == 'filter_date':
            if fiscalyear_id:
                fyear = self.pool.get('account.fiscalyear').browse(
                    cr, uid, fiscalyear_id, context=context)
                date_from = fyear.date_start
                date_to = fyear.date_stop > time.strftime(
                    '%Y-%m-%d') and time.strftime('%Y-%m-%d') \
                    or fyear.date_stop
            else:
                date_from, date_to = time.strftime(
                    '%Y-01-01'), time.strftime('%Y-%m-%d')
            res['value'] = {
                'date_from': date_from,
                'date_to': date_to
            }
        return res

    @api.multi
    def _print_report(self, data):
        # we update form with display account value
        data = self.pre_print_report(data)
        Report = self.env['report'].with_context(landscape=True)
        return Report.get_action(
            self, 'account.report_generalledger_qweb',
            data=data)
