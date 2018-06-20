# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# Copyright 2018 Jacques-Etienne Baudoux (BCIM sprl) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models


class AccountReportGeneralLedgerWizard(models.TransientModel):
    _inherit = 'general.ledger.webkit'

    def _print_report(self, cr, uid, ids, data, context=None):
        context = context or {}
        if context.get('xls_export'):
            # we update form with display account value
            data = self.pre_print_report(cr, uid, ids, data, context=context)
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.account_report_general_ledger_xlsx',
                'datas': data}
        else:
            return super(AccountReportGeneralLedgerWizard, self)._print_report(
                cr, uid, ids, data, context=context)
