# -*- coding: utf-8 -*-
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from openerp.tests.common import TransactionCase


class TestAgedPartnerBalance(TransactionCase):

    def setUp(cls):
        super(TestAgedPartnerBalance, cls).setUp()
        env = cls.env
        model = env['report_aged_partner_balance_qweb']
        main_company = env.ref('base.main_company')

        cls.report = model.create({
            'date_at': time.strftime('%Y-12-31'),
            'company_id': main_company.id,
        })

    def test_01_compute_data(self):
        """Check if data are computed"""
        self.report.compute_data_for_report()
        self.assertGreaterEqual(len(self.report.account_ids), 1)

    def test_02_generation_report_qweb(self):
        """Check if report PDF/HTML is correctly generated"""

        report_name = 'account_financial_report_qweb.' \
                      'report_aged_partner_balance_qweb'
        # Check if returned report action is correct
        report_action = self.report.print_report()
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
        self.assertRegexpMatches(report_html, 'Aged Partner Balance')
        self.assertRegexpMatches(report_html, self.report.account_ids[0].name)
