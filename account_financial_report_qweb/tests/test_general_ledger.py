# -*- coding: utf-8 -*-
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from openerp.tests.common import TransactionCase


class TestGeneralLedger(TransactionCase):

    def setUp(cls):
        super(TestGeneralLedger, cls).setUp()
        env = cls.env
        model = env['report_general_ledger_qweb']
        main_company = env.ref('base.main_company')

        cls.report = model.create({
            'date_from': time.strftime('%Y-01-01'),
            'date_to': time.strftime('%Y-12-31'),
            'company_id': main_company.id,
            'fy_start_date': time.strftime('%Y-01-01'),
        })

    def test_01_compute_data(self):
        """Check if data are computed"""
        self.report.compute_data_for_report()
        self.assertGreaterEqual(len(self.report.account_ids), 1)

    def test_02_generation_report_qweb(self):
        """Check if report PDF/HTML is correctly generated"""

        report_name = 'account_financial_report_qweb.' \
                      'report_general_ledger_qweb'
        # Check if returned report action is correct
        report_action = self.report.print_report(xlsx_report=False)
        self.assertDictContainsSubset(
            {
                'type': 'ir.actions.report.xml',
                'report_name': report_name,
                'report_type': 'qweb-pdf',
            },
            report_action
        )

        # Check if report template is correct
        report_html = self.env['report'].get_html(self.report, report_name)
        self.assertRegexpMatches(report_html, 'General Ledger')
        self.assertRegexpMatches(report_html, self.report.account_ids[0].name)

    def test_03_generation_report_xlsx(self):
        """Check if report XLSX is correctly generated"""

        report_name = 'account_financial_report_qweb.' \
                      'report_general_ledger_xlsx'
        # Check if returned report action is correct
        report_action = self.report.print_report(xlsx_report=True)
        self.assertDictContainsSubset(
            {
                'type': 'ir.actions.report.xml',
                'report_name': report_name,
                'report_type': 'xlsx',
            },
            report_action
        )

        # Check if report template is correct
        action_name = 'account_financial_report_qweb.' \
                      'action_report_general_ledger_xlsx'
        report_xlsx = self.env.ref(action_name).render_report(
            self.report.ids,
            report_name,
            {'report_type': u'xlsx'}
        )
        self.assertGreaterEqual(len(report_xlsx[0]), 1)
        self.assertEqual(report_xlsx[1], 'xlsx')
