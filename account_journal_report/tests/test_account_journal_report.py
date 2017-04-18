# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import fields
from openerp.tests.common import SavepointCase


class TestAccountJournalReport(SavepointCase):
    """
        Tests for Account Journal Report.
    """
    def setUp(self):
        super(TestAccountJournalReport, self).setUp()

        self.report_model = \
            self.env['report.account_journal_report.journal_ledger']
        self.wiz = self.env['account.journal.entries.report']
        self.report_name = 'account_journal_report.journal_ledger'
        self.action_name = 'account_journal_report.' \
                           'account_journal_ledger_report'
        self.report_xlsx_name = 'account_journal_report.journal_ledger_xlsx'
        self.action_xlsx_name = 'account_journal_report.' \
                                'action_account_journal_ledger_xlsx'
        self.report_title = 'Journal Ledger'

        self.today = fields.Date.today()

        self.account_type = self.env['account.account.type'].create({
            'name': 'Test account type',
            'type': 'other',
        })
        self.account = self.env['account.account'].create({
            'name': 'Test account',
            'code': 'TEST',
            'user_type_id': self.account_type.id,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal',
            'code': 'TEST',
            'type': 'general',
        })
        self.move = self.env['account.move'].create({
            'journal_id': self.journal.id,
            'date': fields.Date.today(),
            'line_ids': [
                (0, 0, {
                    'name': 'Debit line',
                    'account_id': self.account.id,
                    'debit': 100,
                }),
                (0, 0, {
                    'name': 'Credit line',
                    'account_id': self.account.id,
                    'credit': 100,
                }),
            ],
        })
        self.move.post()

    def test_account_journal_report(self):

        wiz_id = self.wiz.create({
            'journal_ids': [(6, 0, self.journal.ids)],
            'date_start': self.today,
            'date_end': self.today,
        })
        report = wiz_id.print_report()

        self.assertDictContainsSubset(
            {
                'type': 'ir.actions.report.xml',
                'report_name': self.report_name,
                'report_type': 'qweb-pdf',
            },
            report,
            'There was an error and the PDF report was not generated.'
        )

        data = wiz_id.read()[0]
        report = self.env.ref(self.action_name).\
            render_report(
            wiz_id.ids, self.report_name, data
        )
        self.assertGreaterEqual(len(report[0]), 1)
        self.assertEqual(report[1], 'html')

    def test_account_journal_report_xlsx(self):

        wiz_id = self.wiz.create({
            'journal_ids': [(6, 0, self.journal.ids)],
            'date_start': self.today,
            'date_end': self.today,
        })
        report = wiz_id.print_report_xlsx()

        self.assertDictContainsSubset(
            {
                'type': 'ir.actions.report.xml',
                'report_type': 'xlsx',
                'report_name': self.report_xlsx_name,
            },
            report,
            'There was an error and the XLSX report was not generated.'
        )

        data = wiz_id.read()[0]
        report_xlsx = self.env.ref(self.action_xlsx_name).\
            render_report(
            wiz_id.ids, self.report_xlsx_name, data
        )

        self.assertGreaterEqual(len(report_xlsx[0]), 1)
        self.assertEqual(report_xlsx[1], 'xlsx')
