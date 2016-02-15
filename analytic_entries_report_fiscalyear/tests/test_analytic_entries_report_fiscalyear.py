# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.tests.common import TransactionCase


class TestAnalyticEntriesReportFiscalyear(TransactionCase):
    def test_analytic_entries_report_fiscalyear(self):
        self.env['analytic.entries.report'].read_group(
            [
                ('fiscalyear_id', 'offset', 0),
                ('period_id', 'offset', 0),
            ],
            ['period_id'],
            ['period_id'])
