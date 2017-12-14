# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models


class AgedOpenInvoice(models.TransientModel):
    _inherit = 'aged.open.invoices.webkit'

    # pylint: disable=old-api7-method-defined
    def xls_export(self, cr, uid, ids, context=None):
        return self.check_report(cr, uid, ids, context=context)

    # pylint: disable=old-api7-method-defined
    def _print_report(self, cr, uid, ids, data, context=None):
        context = context or {}
        if context.get('xls_export'):
            # we update form with display account value
            data = self.pre_print_report(cr, uid, ids, data, context=context)
            return {
                'type': 'ir.actions.report.xml',
                'report_name':
                    'account.aged_open_invoices_xls',
                'datas': data}
        else:
            return super(AgedOpenInvoice, self)._print_report(
                cr, uid, ids, data, context=context)
