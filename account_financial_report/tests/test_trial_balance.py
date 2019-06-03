# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from odoo.tests import common
from . import abstract_test_foreign_currency as a_t_f_c


class TestTrialBalance(a_t_f_c.AbstractTestForeignCurrency):
    """
        Technical tests for Trial Balance Report.
    """

    def _getReportModel(self):
        return self.env['report_trial_balance']

    def _getQwebReportName(self):
        return 'account_financial_report.report_trial_balance_qweb'

    def _getXlsxReportName(self):
        return 'a_f_r.report_trial_balance_xlsx'

    def _getXlsxReportActionName(self):
        return 'account_financial_report.action_report_trial_balance_xlsx'

    def _getReportTitle(self):
        return 'Odoo'

    def _getBaseFilters(self):
        return {
            'date_from': time.strftime('%Y-01-01'),
            'date_to': time.strftime('%Y-12-31'),
            'company_id': self.company.id,
            'fy_start_date': time.strftime('%Y-01-01'),
            'foreign_currency': True,
            'show_partner_details': True,
        }

    def _getAdditionalFiltersToBeTested(self):
        return [
            {'only_posted_moves': True},
            {'hide_account_at_0': True},
            {'show_partner_details': True},
            {'hierarchy_on': 'computed'},
            {'hierarchy_on': 'relation'},
            {'only_posted_moves': True, 'hide_account_at_0': True,
             'hierarchy_on': 'computed'},
            {'only_posted_moves': True, 'hide_account_at_0': True,
             'hierarchy_on': 'relation'},
            {'only_posted_moves': True, 'hide_account_at_0': True},
            {'only_posted_moves': True, 'show_partner_details': True},
            {'hide_account_at_0': True, 'show_partner_details': True},
            {
                'only_posted_moves': True,
                'hide_account_at_0': True,
                'show_partner_details': True
            },
        ]

    def _partner_test_is_possible(self, filters):
        return 'show_partner_details' in filters


class TestTrialBalanceReport(common.TransactionCase):

    def setUp(self):
        super(TestTrialBalanceReport, self).setUp()
        group_obj = self.env['account.group']
        acc_obj = self.env['account.account']
        self.group1 = group_obj.create(
            {'code_prefix': '1',
             'name': 'Group 1'})
        self.group11 = group_obj.create(
            {'code_prefix': '11',
             'name': 'Group 11',
             'parent_id': self.group1.id})
        self.group2 = group_obj.create(
            {'code_prefix': '2',
             'name': 'Group 2'})
        self.account100 = acc_obj.create(
            {'code': '100',
             'name': 'Account 100',
             'group_id': self.group1.id,
             'user_type_id': self.env.ref(
                 'account.data_account_type_receivable').id,
             'reconcile': True})
        self.account110 = self.env['account.account'].search([
            (
                'user_type_id',
                '=',
                self.env.ref('account.data_unaffected_earnings').id
            )], limit=1)
        self.account200 = acc_obj.create(
            {'code': '200',
             'name': 'Account 200',
             'group_id': self.group2.id,
             'user_type_id': self.env.ref(
                 'account.data_account_type_other_income').id})
        self.account300 = acc_obj.create(
            {'code': '300',
             'name': 'Account 300',
             'user_type_id': self.env.ref(
                 'account.data_account_type_other_income').id})
        self.account301 = acc_obj.create(
            {'code': '301',
             'name': 'Account 301',
             'group_id': self.group2.id,
             'user_type_id': self.env.ref(
                 'account.data_account_type_other_income').id})
        self.previous_fy_date_start = '2015-01-01'
        self.previous_fy_date_end = '2015-12-31'
        self.fy_date_start = '2016-01-01'
        self.fy_date_end = '2016-12-31'
        self.date_start = '2016-01-01'
        self.date_end = '2016-12-31'

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
        journal = self.env['account.journal'].search([], limit=1)
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
                    'account_id': self.account100.id}),
                (0, 0, {
                    'name': move_name,
                    'debit': income_debit,
                    'credit': income_credit,
                    'account_id': self.account200.id}),
                (0, 0, {
                    'name': move_name,
                    'debit': unaffected_debit,
                    'credit': unaffected_credit,
                    'account_id': self.account110.id}),
                (0, 0, {
                    'name': move_name,
                    'debit': receivable_debit,
                    'credit': receivable_credit,
                    'account_id': self.account300.id}),
                (0, 0, {
                    'name': move_name,
                    'debit': receivable_credit,
                    'credit': receivable_debit,
                    'account_id': self.account301.id})
                ]}
        move = self.env['account.move'].create(move_vals)
        move.post()

    def _get_report_lines(self, with_partners=False, hierarchy_on='computed'):
        company = self.env.ref('base.main_company')
        trial_balance = self.env['report_trial_balance'].create({
            'date_from': self.date_start,
            'date_to': self.date_end,
            'only_posted_moves': True,
            'hide_account_at_0': False,
            'hierarchy_on': hierarchy_on,
            'company_id': company.id,
            'fy_start_date': self.fy_date_start,
            'show_partner_details': with_partners,
            })
        trial_balance.compute_data_for_report()
        lines = {}
        report_account_model = self.env['report_trial_balance_account']
        lines['receivable'] = report_account_model.search([
            ('report_id', '=', trial_balance.id),
            ('account_id', '=', self.account100.id),
        ])
        lines['income'] = report_account_model.search([
            ('report_id', '=', trial_balance.id),
            ('account_id', '=', self.account200.id),
        ])
        lines['unaffected'] = report_account_model.search([
            ('report_id', '=', trial_balance.id),
            ('account_id', '=', self.account110.id),
        ])
        lines['group1'] = report_account_model.search([
            ('report_id', '=', trial_balance.id),
            ('account_group_id', '=', self.group1.id),
        ])
        lines['group2'] = report_account_model.search([
            ('report_id', '=', trial_balance.id),
            ('account_group_id', '=', self.group2.id),
        ])
        if with_partners:
            report_partner_model = self.env[
                'report_trial_balance_partner'
            ]
            lines['partner_receivable'] = report_partner_model.search([
                ('report_account_id', '=', lines['receivable'].id),
                ('partner_id', '=', self.env.ref('base.res_partner_12').id),
            ])
        return lines

    def test_00_account_group(self):
        self.assertGreaterEqual(len(self.group1.compute_account_ids), 19)
        self.assertGreaterEqual(len(self.group2.compute_account_ids), 9)

    def test_01_account_balance_computed(self):
        # Make sure there's no account of type "Current Year Earnings" in the
        # groups - We change the code
        earning_accs = self.env['account.account'].search([
            ('user_type_id', '=',
             self.env.ref('account.data_unaffected_earnings').id)
        ])
        for acc in earning_accs:
            if acc.code.startswith('1') or acc.code.startswith('2'):
                acc.code = '999' + acc.code
        # Generate the general ledger line
        lines = self._get_report_lines()
        self.assertEqual(len(lines['receivable']), 1)
        self.assertEqual(len(lines['income']), 1)

        # Add a move at the previous day of the first day of fiscal year
        # to check the initial balance
        self._add_move(
            date=self.previous_fy_date_end,
            receivable_debit=1000,
            receivable_credit=0,
            income_debit=0,
            income_credit=1000
        )

        # Re Generate the trial balance line
        lines = self._get_report_lines()
        self.assertEqual(len(lines['receivable']), 1)
        self.assertEqual(len(lines['income']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['receivable'].initial_balance, 1000)
        self.assertEqual(lines['receivable'].debit, 0)
        self.assertEqual(lines['receivable'].credit, 0)
        self.assertEqual(lines['receivable'].final_balance, 1000)

        self.assertEqual(lines['group1'].initial_balance, 1000)
        self.assertEqual(lines['group1'].debit, 0)
        self.assertEqual(lines['group1'].credit, 0)
        self.assertEqual(lines['group1'].final_balance, 1000)

        # Add reversed move of the initial move the first day of fiscal year
        # to check the first day of fiscal year is not used
        # to compute the initial balance
        self._add_move(
            date=self.fy_date_start,
            receivable_debit=0,
            receivable_credit=1000,
            income_debit=1000,
            income_credit=0
        )

        # Re Generate the trial balance line
        lines = self._get_report_lines()
        self.assertEqual(len(lines['receivable']), 1)
        self.assertEqual(len(lines['income']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['receivable'].initial_balance, 1000)
        self.assertEqual(lines['receivable'].debit, 0)
        self.assertEqual(lines['receivable'].credit, 1000)
        self.assertEqual(lines['receivable'].final_balance, 0)

        self.assertEqual(lines['income'].initial_balance, 0)
        self.assertEqual(lines['income'].debit, 1000)
        self.assertEqual(lines['income'].credit, 0)
        self.assertEqual(lines['income'].final_balance, 1000)

        self.assertEqual(lines['group1'].initial_balance, 1000)
        self.assertEqual(lines['group1'].debit, 0)
        self.assertEqual(lines['group1'].credit, 1000)
        self.assertEqual(lines['group1'].final_balance, 0)

        self.assertEqual(lines['group2'].initial_balance, 0)
        self.assertEqual(lines['group2'].debit, 1000)
        self.assertEqual(lines['group2'].credit, 0)
        self.assertEqual(lines['group2'].final_balance, 1000)

        # Add another move at the end day of fiscal year
        # to check that it correctly used on report
        self._add_move(
            date=self.fy_date_end,
            receivable_debit=0,
            receivable_credit=1000,
            income_debit=1000,
            income_credit=0
        )

        # Re Generate the trial balance line
        lines = self._get_report_lines()
        self.assertEqual(len(lines['receivable']), 1)
        self.assertEqual(len(lines['income']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['receivable'].initial_balance, 1000)
        self.assertEqual(lines['receivable'].debit, 0)
        self.assertEqual(lines['receivable'].credit, 2000)
        self.assertEqual(lines['receivable'].final_balance, -1000)

        self.assertEqual(lines['income'].initial_balance, 0)
        self.assertEqual(lines['income'].debit, 2000)
        self.assertEqual(lines['income'].credit, 0)
        self.assertEqual(lines['income'].final_balance, 2000)

        self.assertEqual(lines['group1'].initial_balance, 1000)
        self.assertEqual(lines['group1'].debit, 0)
        self.assertEqual(lines['group1'].credit, 2000)
        self.assertEqual(lines['group1'].final_balance, -1000)

        self.assertEqual(lines['group2'].initial_balance, 0)
        self.assertEqual(lines['group2'].debit, 2000)
        self.assertEqual(lines['group2'].credit, 0)
        self.assertEqual(lines['group2'].final_balance, 2000)
        self.assertGreaterEqual(len(lines['group2'].compute_account_ids), 9)

    def test_02_account_balance_hierarchy(self):
        # Generate the general ledger line
        lines = self._get_report_lines(hierarchy_on='relation')
        self.assertEqual(len(lines['receivable']), 1)
        self.assertEqual(len(lines['income']), 1)

        # Add a move at the previous day of the first day of fiscal year
        # to check the initial balance
        self._add_move(
            date=self.previous_fy_date_end,
            receivable_debit=1000,
            receivable_credit=0,
            income_debit=0,
            income_credit=1000
        )

        # Re Generate the trial balance line
        lines = self._get_report_lines(hierarchy_on='relation')
        self.assertEqual(len(lines['receivable']), 1)
        self.assertEqual(len(lines['income']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['receivable'].initial_balance, 1000)
        self.assertEqual(lines['receivable'].debit, 0)
        self.assertEqual(lines['receivable'].credit, 0)
        self.assertEqual(lines['receivable'].final_balance, 1000)

        self.assertEqual(lines['group1'].initial_balance, 1000)
        self.assertEqual(lines['group1'].debit, 0)
        self.assertEqual(lines['group1'].credit, 0)
        self.assertEqual(lines['group1'].final_balance, 1000)

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

        # Re Generate the trial balance line
        lines = self._get_report_lines(hierarchy_on='relation')
        self.assertEqual(len(lines['receivable']), 1)
        self.assertEqual(len(lines['income']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['receivable'].initial_balance, 1000)
        self.assertEqual(lines['receivable'].debit, 0)
        self.assertEqual(lines['receivable'].credit, 1000)
        self.assertEqual(lines['receivable'].final_balance, 0)

        self.assertEqual(lines['income'].initial_balance, 0)
        self.assertEqual(lines['income'].debit, 1000)
        self.assertEqual(lines['income'].credit, 0)
        self.assertEqual(lines['income'].final_balance, 1000)

        self.assertEqual(lines['group1'].initial_balance, 1000)
        self.assertEqual(lines['group1'].debit, 0)
        self.assertEqual(lines['group1'].credit, 1000)
        self.assertEqual(lines['group1'].final_balance, 0)

        self.assertEqual(lines['group2'].initial_balance, 0)
        self.assertEqual(lines['group2'].debit, 2000)
        self.assertEqual(lines['group2'].credit, 0)
        self.assertEqual(lines['group2'].final_balance, 2000)
        self.assertEqual(len(lines['group2'].compute_account_ids), 2)
        # Add another move at the end day of fiscal year
        # to check that it correctly used on report
        self._add_move(
            date=self.fy_date_end,
            receivable_debit=0,
            receivable_credit=1000,
            income_debit=1000,
            income_credit=0
        )

        # Re Generate the trial balance line
        lines = self._get_report_lines(hierarchy_on='relation')
        self.assertEqual(len(lines['receivable']), 1)
        self.assertEqual(len(lines['income']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['receivable'].initial_balance, 1000)
        self.assertEqual(lines['receivable'].debit, 0)
        self.assertEqual(lines['receivable'].credit, 2000)
        self.assertEqual(lines['receivable'].final_balance, -1000)

        self.assertEqual(lines['income'].initial_balance, 0)
        self.assertEqual(lines['income'].debit, 2000)
        self.assertEqual(lines['income'].credit, 0)
        self.assertEqual(lines['income'].final_balance, 2000)

        self.assertEqual(lines['group1'].initial_balance, 1000)
        self.assertEqual(lines['group1'].debit, 0)
        self.assertEqual(lines['group1'].credit, 2000)
        self.assertEqual(lines['group1'].final_balance, -1000)

        self.assertEqual(lines['group2'].initial_balance, 0)
        self.assertEqual(lines['group2'].debit, 4000)
        self.assertEqual(lines['group2'].credit, 0)
        self.assertEqual(lines['group2'].final_balance, 4000)

    def test_03_partner_balance(self):
        # Generate the trial balance line
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

        # Re Generate the trial balance line
        lines = self._get_report_lines(with_partners=True)
        self.assertEqual(len(lines['partner_receivable']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['partner_receivable'].initial_balance, 1000)
        self.assertEqual(lines['partner_receivable'].debit, 0)
        self.assertEqual(lines['partner_receivable'].credit, 0)
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

        # Re Generate the trial balance line
        lines = self._get_report_lines(with_partners=True)
        self.assertEqual(len(lines['partner_receivable']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['partner_receivable'].initial_balance, 1000)
        self.assertEqual(lines['partner_receivable'].debit, 0)
        self.assertEqual(lines['partner_receivable'].credit, 1000)
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

        # Re Generate the trial balance line
        lines = self._get_report_lines(with_partners=True)
        self.assertEqual(len(lines['partner_receivable']), 1)

        # Check the initial and final balance
        self.assertEqual(lines['partner_receivable'].initial_balance, 1000)
        self.assertEqual(lines['partner_receivable'].debit, 0)
        self.assertEqual(lines['partner_receivable'].credit, 2000)
        self.assertEqual(lines['partner_receivable'].final_balance, -1000)

    def test_04_undistributed_pl(self):
        # Add a P&L Move in the previous FY
        move_name = 'current year pl move'
        journal = self.env['account.journal'].search([], limit=1)
        move_vals = {
            'journal_id': journal.id,
            'name': move_name,
            'date': self.previous_fy_date_end,
            'line_ids': [
                (0, 0, {
                    'name': move_name,
                    'debit': 0.0,
                    'credit': 1000.0,
                    'account_id': self.account300.id}),
                (0, 0, {
                    'name': move_name,
                    'debit': 1000.0,
                    'credit': 0.0,
                    'account_id': self.account100.id})
            ]}
        move = self.env['account.move'].create(move_vals)
        move.post()
        # Generate the trial balance line
        report_account_model = self.env['report_trial_balance_account']
        company = self.env.ref('base.main_company')
        trial_balance = self.env['report_trial_balance'].create({
            'date_from': self.date_start,
            'date_to': self.date_end,
            'only_posted_moves': True,
            'hide_account_at_0': False,
            'hierarchy_on': 'none',
            'company_id': company.id,
            'fy_start_date': self.fy_date_start,
            })
        trial_balance.compute_data_for_report()

        unaffected_balance_lines = report_account_model.search([
            ('report_id', '=', trial_balance.id),
            ('account_id', '=', self.account110.id),
        ])
        self.assertEqual(len(unaffected_balance_lines), 1)
        self.assertEqual(unaffected_balance_lines[0].initial_balance, -1000)
        self.assertEqual(unaffected_balance_lines[0].debit, 0)
        self.assertEqual(unaffected_balance_lines[0].credit, 0)
        self.assertEqual(unaffected_balance_lines[0].final_balance, -1000)
        # Add a P&L Move to the current FY
        move_name = 'current year pl move'
        journal = self.env['account.journal'].search([], limit=1)
        move_vals = {
            'journal_id': journal.id,
            'name': move_name,
            'date': self.date_start,
            'line_ids': [
                (0, 0, {
                    'name': move_name,
                    'debit': 0.0,
                    'credit': 1000.0,
                    'account_id': self.account300.id}),
                (0, 0, {
                    'name': move_name,
                    'debit': 1000.0,
                    'credit': 0.0,
                    'account_id': self.account100.id})
                ]}
        move = self.env['account.move'].create(move_vals)
        move.post()
        # Re Generate the trial balance line
        trial_balance = self.env['report_trial_balance'].create({
            'date_from': self.date_start,
            'date_to': self.date_end,
            'only_posted_moves': True,
            'hide_account_at_0': False,
            'hierarchy_on': 'none',
            'company_id': company.id,
            'fy_start_date': self.fy_date_start,
        })
        trial_balance.compute_data_for_report()
        unaffected_balance_lines = report_account_model.search([
            ('report_id', '=', trial_balance.id),
            ('account_id', '=', self.account110.id),
        ])
        # The unaffected earnings account is not affected by a journal entry
        # made to the P&L in the current fiscal year.
        self.assertEqual(len(unaffected_balance_lines), 1)
        self.assertEqual(unaffected_balance_lines[0].initial_balance, -1000)
        self.assertEqual(unaffected_balance_lines[0].debit, 0)
        self.assertEqual(unaffected_balance_lines[0].credit, 0)
        self.assertEqual(unaffected_balance_lines[0].final_balance, -1000)
        # Add a Move including Unaffected Earnings to the current FY
        move_name = 'current year unaffected earnings move'
        journal = self.env['account.journal'].search([], limit=1)
        move_vals = {
            'journal_id': journal.id,
            'name': move_name,
            'date': self.date_start,
            'line_ids': [
                (0, 0, {
                    'name': move_name,
                    'debit': 0.0,
                    'credit': 1000.0,
                    'account_id': self.account110.id}),
                (0, 0, {
                    'name': move_name,
                    'debit': 1000.0,
                    'credit': 0.0,
                    'account_id': self.account100.id})
            ]}
        move = self.env['account.move'].create(move_vals)
        move.post()
        # Re Generate the trial balance line
        trial_balance = self.env['report_trial_balance'].create({
            'date_from': self.date_start,
            'date_to': self.date_end,
            'only_posted_moves': True,
            'hide_account_at_0': False,
            'hierarchy_on': 'none',
            'company_id': company.id,
            'fy_start_date': self.fy_date_start,
        })
        trial_balance.compute_data_for_report()
        # The unaffected earnings account affected by a journal entry
        # made to the unaffected earnings in the current fiscal year.
        unaffected_balance_lines = report_account_model.search([
            ('report_id', '=', trial_balance.id),
            ('account_id', '=', self.account110.id),
        ])
        self.assertEqual(len(unaffected_balance_lines), 1)
        self.assertEqual(unaffected_balance_lines[0].initial_balance, -1000)
        self.assertEqual(unaffected_balance_lines[0].debit, 0)
        self.assertEqual(unaffected_balance_lines[0].credit, 1000)
        self.assertEqual(unaffected_balance_lines[0].final_balance, -2000)
        # The totals for the Trial Balance are zero
        all_lines = report_account_model.search([
            ('report_id', '=', trial_balance.id),
        ])
        self.assertEqual(sum(all_lines.mapped('initial_balance')), 0)
        self.assertEqual(sum(all_lines.mapped('final_balance')), 0)
        self.assertEqual(sum(all_lines.mapped('debit')),
                         sum(all_lines.mapped('credit')))
