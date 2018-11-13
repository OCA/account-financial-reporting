# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from odoo.tests.common import TransactionCase


class TestAccountingReport(TransactionCase):

    def setUp(self):
        super(TestAccountingReport, self).setUp()
        p_type = self.env['date.range.type'].create({
            'name': 'Fiscal Period',
            'allow_overlap': False})
        self.p1 = self.env['date.range'].create({
            'name': 'P01',
            'type_id': p_type.id,
            'date_start': time.strftime('%Y-01-01'),
            'date_end': time.strftime('%Y-01-31')})

    def test_accounting_report(self):
        bs = self.env.ref(
            'account.account_financial_report_balancesheet0')
        wiz = self.env['accounting.report'].create({
            'account_report_id': bs.id})

        # Check date_range onchange
        wiz.date_range_id = self.p1
        wiz._onchange_date_range_id()
        self.assertEquals(wiz.date_from, time.strftime('%Y-01-01'))
