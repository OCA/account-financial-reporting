# -*- coding: utf-8 -*-
# Copyright 2014 Camptocamp SA, Nicolas Bessi.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields


class AccountAgedTrialBalance(models.TransientModel):
    """Will launch age partner balance report.
    This report is based on Open Invoice Report
    and share a lot of knowledge with him
    """

    _inherit = "open.invoices.webkit"
    _name = "account.aged.trial.balance.webkit"
    _description = "Aged partner balanced"

    # pylint: disable=old-api7-method-defined
    def _get_current_fiscalyear(self, cr, uid, context=None):
        return self.pool['account.fiscalyear'].find(cr, uid, context=context)

    filter = fields.Selection(
        [('filter_period', 'Periods')], "Filter by", required=True,
        default='filter_period'
    )
    fiscalyear_id = fields.Many2one(
        'account.fiscalyear', 'Fiscal Year', required=True,
        default=lambda self: self._get_current_fiscalyear()
    )
    period_to = fields.Many2one('account.period', 'End Period', required=True)

    # pylint: disable=old-api7-method-defined
    def onchange_fiscalyear(self, cr, uid, ids, fiscalyear=False,
                            period_id=False, date_to=False, until_date=False,
                            context=None):
        res = super(AccountAgedTrialBalance, self).onchange_fiscalyear(
            cr, uid, ids, fiscalyear=fiscalyear, period_id=period_id,
            date_to=date_to, until_date=until_date, context=context
        )
        filters = self.onchange_filter(cr, uid, ids, filter='filter_period',
                                       fiscalyear_id=fiscalyear,
                                       context=context)
        res['value'].update({
            'period_from': filters['value']['period_from'],
            'period_to': filters['value']['period_to'],
        })
        return res

    # pylint: disable=old-api7-method-defined
    def _print_report(self, cr, uid, ids, data, context=None):
        # we update form with display account value
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.account_aged_trial_balance_webkit',
                'datas': data}
