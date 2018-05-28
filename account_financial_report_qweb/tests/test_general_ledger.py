# -*- coding: utf-8 -*-
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from odoo.tests import common
from . import abstract_test_foreign_currency as a_t_f_c


class TestGeneralLedger(a_t_f_c.AbstractTestForeignCurrency):
    """
        Technical tests for General Ledger Report.
    """

    def _getReportModel(self):
        return self.env['report_general_ledger_qweb']

    def _getQwebReportName(self):
        return 'account_financial_report_qweb.report_general_ledger_qweb'

    def _getXlsxReportName(self):
        return 'account_financial_report_qweb.report_general_ledger_xlsx'

    def _getXlsxReportActionName(self):
        return 'account_financial_report_qweb.' \
               'action_report_general_ledger_xlsx'

    def _getReportTitle(self):
        return 'General Ledger'

    def _getBaseFilters(self):
        return {
            'date_from': time.strftime('%Y-01-01'),
            'date_to': time.strftime('%Y-12-31'),
            'company_id': self.company.id,
            'fy_start_date': time.strftime('%Y-01-01'),
            'foreign_currency': True,
        }

    def _getAdditionalFiltersToBeTested(self):
        return [
            {'only_posted_moves': True},
            {'hide_account_balance_at_0': True},
            {'centralize': True},
            {'only_posted_moves': True, 'hide_account_balance_at_0': True},
            {'only_posted_moves': True, 'centralize': True},
            {'hide_account_balance_at_0': True, 'centralize': True},
            {
                'only_posted_moves': True,
                'hide_account_balance_at_0': True,
                'centralize': True
            },
        ]


@common.at_install(False)
@common.post_install(True)
class TestGeneralLedgerReport(common.TransactionCase):

    def setUp(self):
        super(TestGeneralLedgerReport, self).setUp()
        self.before_previous_fy_year = '2014-05-05'
        self.previous_fy_date_start = '2015-01-01'
        self.previous_fy_date_end = '2015-12-31'
        self.fy_date_start = '2016-01-01'
        self.fy_date_end = '2016-12-31'
        self.receivable_account = self.env['account.account'].search([
            ('user_type_id.name', '=', 'Receivable')
            ], limit=1)
        self.income_account = self.env['account.account'].search([
            ('user_type_id.name', '=', 'Income')
            ], limit=1)
        self.unaffected_account = self.env['account.account'].search([
            (
                'user_type_id',
                '=',
                self.env.ref('account.data_unaffected_earnings').id
            )], limit=1)

    def _add_move(
        self,
        date,
        receivable_debit,
        receivable_credit,
        income_debit,
        income_credit,
        unaffected_debit=0,
        unaffected_credit=0
    ):
        move_name = 'expense accrual'
        journal = self.env['account.journal'].search([
            ('code', '=', 'MISC')])
        partner = self.env.ref('base.res_partner_12')
        move_vals = {
            'journal_id': journal.id,
            'partner_id': partner.id,
            'name': move_name,
            'date': date,
            'line_ids': [
                (0, 0, {
                    'name': move_name,
                    'debit': receivable_debit,
                    'credit': receivable_credit,
                    'account_id': self.receivable_account.id}),
                (0, 0, {
                    'name': move_name,
                    'debit': income_debit,
                    'credit': income_credit,
                    'account_id': self.income_account.id}),
                (0, 0, {
                    'name': move_name,
                    'debit': unaffected_debit,
                    'credit': unaffected_credit,
                    'account_id': self.unaffected_account.id}),
                ]}
        move = self.env['account.move'].create(move_vals)
        move.post()

    def _get_report_lines(self, with_partners=False):
        company = self.env.ref('base.main_company')
        general_ledger = self.env['report_general_ledger_qweb'].create({
            'date_from': self.fy_date_start,
            'date_to': self.fy_date_end,
            'only_posted_moves': True,
            'hide_account_balance_at_0': False,
            'company_id': company.id,
            'fy_start_date': self.fy_date_start,
            })
        general_ledger.compute_data_for_report(
            with_line_details=True, with_partners=with_partners
        )
        lines = {}
        report_account_model = self.env['report_general_ledger_qweb_account']
        lines['receivable'] = report_account_model.search([
            ('report_id', '=', general_ledger.id),
            ('account_id', '=', self.receivable_account.id),
        ])
        lines['income'] = report_account_model.search([
            ('report_id', '=', general_ledger.id),
            ('account_id', '=', self.income_account.id),
        ])
        lines['unaffected'] = report_account_model.search([
            ('report_id', '=', general_ledger.id),
            ('account_id', '=', self.unaffected_account.id),
        ])
        if with_partners:
            report_partner_model = self.env[
                'report_general_ledger_qweb_partner'
            ]
            lines['partner_receivable'] = report_partner_model.search([
                ('report_account_id', '=', lines['receivable'].id),
                ('partner_id', '=', self.env.ref('base.res_partner_12').id),
            ])
        return lines

    def test_01_account_balance(self):
        # Generate the general ledger line
        lines = self._get_report_lines()
        self.assertEqual(len(lines['receivable']), 0)
        self.assertEqual(len(lines['income']), 0)

        # Add a move at the previous day of the first day of fiscal year
        # to check the initial balance
        self._add_move(
            date=self.previous_fy_date_end,
            receivable_debit=1000,
            receivable_credit=0,
            income_debit=0,
            income_credit=1000
        )

        # Re Generate the general ledger line
        lines = self._get_report_lines()
        self.assertEqual(len(lines['receivable']), 1)
        self.assertEqual(len(lines['income']), 0)

        # Check the initial and final balance
        self.assertEqual(lines['receivable'].initial_debit, 1000)
        self.assertEqual(lines['receivable'].initial_credit, 0)
        self.assertEqual(lines['receivable'].initial_balance, 1000)
        self.assertEqual(lines['receivable'].final_debit, 1000)
        self.assertEqual(lines['receivable'].final_credit, 0)
        self.assertEqual(lines['receivable'].final_balance, 1000)

        # Add reversale move of the initial move the first day of fiscal year
        # to check the first day of fiscal year is not used
        # to compute the initial balance
        self._add_move(
            date=self.fy_date_start,
            receivable_debit=0,
            receivable_credit=1000,
            income_debit=1000,
            income_credit=0
        )

        # Re Generate the general ledger line
        lines = self._get_report_lines()
        self.assertEqual(len(lines['receivable']), 1)
        self.assertEqual(len(lines['income']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['receivable'].initial_debit, 1000)
        self.assertEqual(lines['receivable'].initial_credit, 0)
        self.assertEqual(lines['receivable'].initial_balance, 1000)
        self.assertEqual(lines['receivable'].final_debit, 1000)
        self.assertEqual(lines['receivable'].final_credit, 1000)
        self.assertEqual(lines['receivable'].final_balance, 0)

        self.assertEqual(lines['income'].initial_debit, 0)
        self.assertEqual(lines['income'].initial_credit, 0)
        self.assertEqual(lines['income'].initial_balance, 0)
        self.assertEqual(lines['income'].final_debit, 1000)
        self.assertEqual(lines['income'].final_credit, 0)
        self.assertEqual(lines['income'].final_balance, 1000)

        # Add another move at the end day of fiscal year
        # to check that it correctly used on report
        self._add_move(
            date=self.fy_date_end,
            receivable_debit=0,
            receivable_credit=1000,
            income_debit=1000,
            income_credit=0
        )

        # Re Generate the general ledger line
        lines = self._get_report_lines()
        self.assertEqual(len(lines['receivable']), 1)
        self.assertEqual(len(lines['income']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['receivable'].initial_debit, 1000)
        self.assertEqual(lines['receivable'].initial_credit, 0)
        self.assertEqual(lines['receivable'].initial_balance, 1000)
        self.assertEqual(lines['receivable'].final_debit, 1000)
        self.assertEqual(lines['receivable'].final_credit, 2000)
        self.assertEqual(lines['receivable'].final_balance, -1000)

        self.assertEqual(lines['income'].initial_debit, 0)
        self.assertEqual(lines['income'].initial_credit, 0)
        self.assertEqual(lines['income'].initial_balance, 0)
        self.assertEqual(lines['income'].final_debit, 2000)
        self.assertEqual(lines['income'].final_credit, 0)
        self.assertEqual(lines['income'].final_balance, 2000)

    def test_02_partner_balance(self):
        # Generate the general ledger line
        lines = self._get_report_lines(with_partners=True)
        self.assertEqual(len(lines['partner_receivable']), 0)

        # Add a move at the previous day of the first day of fiscal year
        # to check the initial balance
        self._add_move(
            date=self.previous_fy_date_end,
            receivable_debit=1000,
            receivable_credit=0,
            income_debit=0,
            income_credit=1000
        )

        # Re Generate the general ledger line
        lines = self._get_report_lines(with_partners=True)
        self.assertEqual(len(lines['partner_receivable']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['partner_receivable'].initial_debit, 1000)
        self.assertEqual(lines['partner_receivable'].initial_credit, 0)
        self.assertEqual(lines['partner_receivable'].initial_balance, 1000)
        self.assertEqual(lines['partner_receivable'].final_debit, 1000)
        self.assertEqual(lines['partner_receivable'].final_credit, 0)
        self.assertEqual(lines['partner_receivable'].final_balance, 1000)

        # Add reversale move of the initial move the first day of fiscal year
        # to check the first day of fiscal year is not used
        # to compute the initial balance
        self._add_move(
            date=self.fy_date_start,
            receivable_debit=0,
            receivable_credit=1000,
            income_debit=1000,
            income_credit=0
        )

        # Re Generate the general ledger line
        lines = self._get_report_lines(with_partners=True)
        self.assertEqual(len(lines['partner_receivable']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['partner_receivable'].initial_debit, 1000)
        self.assertEqual(lines['partner_receivable'].initial_credit, 0)
        self.assertEqual(lines['partner_receivable'].initial_balance, 1000)
        self.assertEqual(lines['partner_receivable'].final_debit, 1000)
        self.assertEqual(lines['partner_receivable'].final_credit, 1000)
        self.assertEqual(lines['partner_receivable'].final_balance, 0)

        # Add another move at the end day of fiscal year
        # to check that it correctly used on report
        self._add_move(
            date=self.fy_date_end,
            receivable_debit=0,
            receivable_credit=1000,
            income_debit=1000,
            income_credit=0
        )

        # Re Generate the general ledger line
        lines = self._get_report_lines(with_partners=True)
        self.assertEqual(len(lines['partner_receivable']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['partner_receivable'].initial_debit, 1000)
        self.assertEqual(lines['partner_receivable'].initial_credit, 0)
        self.assertEqual(lines['partner_receivable'].initial_balance, 1000)
        self.assertEqual(lines['partner_receivable'].final_debit, 1000)
        self.assertEqual(lines['partner_receivable'].final_credit, 2000)
        self.assertEqual(lines['partner_receivable'].final_balance, -1000)

    def test_03_unaffected_account_balance(self):
        # Generate the general ledger line
        lines = self._get_report_lines()
        self.assertEqual(len(lines['unaffected']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['unaffected'].initial_debit, 0)
        self.assertEqual(lines['unaffected'].initial_credit, 0)
        self.assertEqual(lines['unaffected'].initial_balance, 0)
        self.assertEqual(lines['unaffected'].final_debit, 0)
        self.assertEqual(lines['unaffected'].final_credit, 0)
        self.assertEqual(lines['unaffected'].final_balance, 0)

        # Add a move at the previous day of the first day of fiscal year
        # to check the initial balance
        self._add_move(
            date=self.previous_fy_date_end,
            receivable_debit=1000,
            receivable_credit=0,
            income_debit=0,
            income_credit=1000
        )

        # Re Generate the general ledger line
        lines = self._get_report_lines()
        self.assertEqual(len(lines['unaffected']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['unaffected'].initial_debit, 0)
        self.assertEqual(lines['unaffected'].initial_credit, 0)
        self.assertEqual(lines['unaffected'].initial_balance, -1000)
        self.assertEqual(lines['unaffected'].final_debit, -0)
        self.assertEqual(lines['unaffected'].final_credit, 0)
        self.assertEqual(lines['unaffected'].final_balance, -1000)

        # Add reversale move of the initial move the first day of fiscal year
        # to check the first day of fiscal year is not used
        # to compute the initial balance
        self._add_move(
            date=self.fy_date_start,
            receivable_debit=0,
            receivable_credit=0,
            income_debit=0,
            income_credit=1000,
            unaffected_debit=1000,
            unaffected_credit=0
        )

        # Re Generate the general ledger line
        lines = self._get_report_lines()
        self.assertEqual(len(lines['unaffected']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['unaffected'].initial_debit, 0)
        self.assertEqual(lines['unaffected'].initial_credit, 0)
        self.assertEqual(lines['unaffected'].initial_balance, -1000)
        self.assertEqual(lines['unaffected'].final_debit, 0)
        self.assertEqual(lines['unaffected'].final_credit, 0)
        self.assertEqual(lines['unaffected'].final_balance, -1000)

        # Add another move at the end day of fiscal year
        # to check that it correctly used on report
        self._add_move(
            date=self.fy_date_end,
            receivable_debit=3000,
            receivable_credit=0,
            income_debit=0,
            income_credit=0,
            unaffected_debit=0,
            unaffected_credit=3000
        )

        # Re Generate the general ledger line
        lines = self._get_report_lines()
        self.assertEqual(len(lines['unaffected']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['unaffected'].initial_debit, 0)
        self.assertEqual(lines['unaffected'].initial_credit, 0)
        self.assertEqual(lines['unaffected'].initial_balance, -1000)
        self.assertEqual(lines['unaffected'].final_debit, 0)
        self.assertEqual(lines['unaffected'].final_credit, 0)
        self.assertEqual(lines['unaffected'].final_balance, -4000)

    def test_04_unaffected_account_balance_2_years(self):
        # Generate the general ledger line
        lines = self._get_report_lines()
        self.assertEqual(len(lines['unaffected']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['unaffected'].initial_debit, 0)
        self.assertEqual(lines['unaffected'].initial_credit, 0)
        self.assertEqual(lines['unaffected'].initial_balance, 0)
        self.assertEqual(lines['unaffected'].final_debit, 0)
        self.assertEqual(lines['unaffected'].final_credit, 0)
        self.assertEqual(lines['unaffected'].final_balance, 0)

        # Add a move at any date 2 years before the balance
        # (to create an historic)
        self._add_move(
            date=self.before_previous_fy_year,
            receivable_debit=0,
            receivable_credit=1000,
            income_debit=1000,
            income_credit=0
        )

        # Re Generate the general ledger line
        lines = self._get_report_lines()
        self.assertEqual(len(lines['unaffected']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['unaffected'].initial_debit, 0)
        self.assertEqual(lines['unaffected'].initial_credit, 0)
        self.assertEqual(lines['unaffected'].initial_balance, 1000)
        self.assertEqual(lines['unaffected'].final_debit, 0)
        self.assertEqual(lines['unaffected'].final_credit, 0)
        self.assertEqual(lines['unaffected'].final_balance, 1000)

        # Affect the company's result last year
        self._add_move(
            date=self.previous_fy_date_start,
            receivable_debit=1000,
            receivable_credit=0,
            income_debit=0,
            income_credit=0,
            unaffected_debit=0,
            unaffected_credit=1000
        )

        # Add another move last year to test the initial balance this year
        self._add_move(
            date=self.previous_fy_date_start,
            receivable_debit=0,
            receivable_credit=500,
            income_debit=500,
            income_credit=0,
            unaffected_debit=0,
            unaffected_credit=0
        )
        # Re Generate the general ledger line
        lines = self._get_report_lines()
        self.assertEqual(len(lines['unaffected']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['unaffected'].initial_debit, 0)
        self.assertEqual(lines['unaffected'].initial_credit, 0)
        self.assertEqual(lines['unaffected'].initial_balance, 500)
        self.assertEqual(lines['unaffected'].final_debit, 0)
        self.assertEqual(lines['unaffected'].final_credit, 0)
        self.assertEqual(lines['unaffected'].final_balance, 500)
