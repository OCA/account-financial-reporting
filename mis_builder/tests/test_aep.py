# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import datetime
import time

from odoo import fields
import odoo.tests.common as common
from odoo.tools.safe_eval import safe_eval

from ..models.aep import AccountingExpressionProcessor as AEP
from ..models.accounting_none import AccountingNone


class TestAEP(common.TransactionCase):

    def setUp(self):
        super(TestAEP, self).setUp()
        self.res_company = self.env['res.company']
        self.account_model = self.env['account.account']
        self.move_model = self.env['account.move']
        self.journal_model = self.env['account.journal']
        self.curr_year = datetime.date.today().year
        self.prev_year = self.curr_year - 1
        # create company
        self.company = self.res_company.create({
            'name': 'AEP Company'})
        # create receivable bs account
        type_ar = self.browse_ref('account.data_account_type_receivable')
        self.account_ar = self.account_model.create({
            'company_id': self.company.id,
            'code': '400AR',
            'name': 'Receivable',
            'user_type_id': type_ar.id,
            'reconcile': True})
        # create income pl account
        type_in = self.browse_ref('account.data_account_type_revenue')
        self.account_in = self.account_model.create({
            'company_id': self.company.id,
            'code': '700IN',
            'name': 'Income',
            'user_type_id': type_in.id})
        # create journal
        self.journal = self.journal_model.create({
            'company_id': self.company.id,
            'name': 'Sale journal',
            'code': 'VEN',
            'type': 'sale'})
        # create move in december last year
        self._create_move(
            date=datetime.date(self.prev_year, 12, 1),
            amount=100,
            debit_acc=self.account_ar,
            credit_acc=self.account_in)
        # create move in january this year
        self._create_move(
            date=datetime.date(self.curr_year, 1, 1),
            amount=300,
            debit_acc=self.account_ar,
            credit_acc=self.account_in)
        # create move in february this year
        self._create_move(
            date=datetime.date(self.curr_year, 3, 1),
            amount=500,
            debit_acc=self.account_ar,
            credit_acc=self.account_in)
        # create the AEP, and prepare the expressions we'll need
        self.aep = AEP(self.company)
        self.aep.parse_expr("bali[]")
        self.aep.parse_expr("bale[]")
        self.aep.parse_expr("balp[]")
        self.aep.parse_expr("balu[]")
        self.aep.parse_expr("bali[700IN]")
        self.aep.parse_expr("bale[700IN]")
        self.aep.parse_expr("balp[700IN]")
        self.aep.parse_expr("bali[400AR]")
        self.aep.parse_expr("bale[400AR]")
        self.aep.parse_expr("balp[400AR]")
        self.aep.parse_expr("debp[400A%]")
        self.aep.parse_expr("crdp[700I%]")
        self.aep.parse_expr("bal_700IN")  # deprecated
        self.aep.parse_expr("bals[700IN]")  # deprecated
        self.aep.done_parsing()

    def _create_move(self, date, amount, debit_acc, credit_acc):
        move = self.move_model.create({
            'journal_id': self.journal.id,
            'date': fields.Date.to_string(date),
            'line_ids': [(0, 0, {
                'name': '/',
                'debit': amount,
                'account_id': debit_acc.id,
            }), (0, 0, {
                'name': '/',
                'credit': amount,
                'account_id': credit_acc.id,
            })]})
        move.post()
        return move

    def _do_queries(self, date_from, date_to):
        self.aep.do_queries(
            date_from=fields.Date.to_string(date_from),
            date_to=fields.Date.to_string(date_to),
            target_move='posted')

    def _eval(self, expr):
        eval_dict = {'AccountingNone': AccountingNone}
        return safe_eval(self.aep.replace_expr(expr), eval_dict)

    def _eval_by_account_id(self, expr):
        res = {}
        eval_dict = {'AccountingNone': AccountingNone}
        for account_id, replaced_exprs in \
                self.aep.replace_exprs_by_account_id([expr]):
            res[account_id] = safe_eval(replaced_exprs[0], eval_dict)
        return res

    def test_sanity_check(self):
        self.assertEquals(self.company.fiscalyear_last_day, 31)
        self.assertEquals(self.company.fiscalyear_last_month, 12)

    def test_aep_basic(self):
        # let's query for december
        self._do_queries(
            datetime.date(self.prev_year, 12, 1),
            datetime.date(self.prev_year, 12, 31))
        # initial balance must be None
        self.assertIs(self._eval('bali[400AR]'), AccountingNone)
        self.assertIs(self._eval('bali[700IN]'), AccountingNone)
        # check variation
        self.assertEquals(self._eval('balp[400AR]'), 100)
        self.assertEquals(self._eval('balp[700IN]'), -100)
        # check ending balance
        self.assertEquals(self._eval('bale[400AR]'), 100)
        self.assertEquals(self._eval('bale[700IN]'), -100)

        # let's query for January
        self._do_queries(
            datetime.date(self.curr_year, 1, 1),
            datetime.date(self.curr_year, 1, 31))
        # initial balance is None for income account (it's not carried over)
        self.assertEquals(self._eval('bali[400AR]'), 100)
        self.assertIs(self._eval('bali[700IN]'), AccountingNone)
        # check variation
        self.assertEquals(self._eval('balp[400AR]'), 300)
        self.assertEquals(self._eval('balp[700IN]'), -300)
        # check ending balance
        self.assertEquals(self._eval('bale[400AR]'), 400)
        self.assertEquals(self._eval('bale[700IN]'), -300)

        # let's query for March
        self._do_queries(
            datetime.date(self.curr_year, 3, 1),
            datetime.date(self.curr_year, 3, 31))
        # initial balance is the ending balance fo January
        self.assertEquals(self._eval('bali[400AR]'), 400)
        self.assertEquals(self._eval('bali[700IN]'), -300)
        # check variation
        self.assertEquals(self._eval('balp[400AR]'), 500)
        self.assertEquals(self._eval('balp[700IN]'), -500)
        # check ending balance
        self.assertEquals(self._eval('bale[400AR]'), 900)
        self.assertEquals(self._eval('bale[700IN]'), -800)
        # check some variant expressions, for coverage
        self.assertEquals(self._eval('crdp[700I%]'), 500)
        self.assertEquals(self._eval('debp[400A%]'), 500)
        self.assertEquals(self._eval('bal_700IN'), -500)
        self.assertEquals(self._eval('bals[700IN]'), -800)

        # unallocated p&l from previous year
        self.assertEquals(self._eval('balu[]'), -100)

        # TODO allocate profits, and then...

    def test_aep_by_account(self):
        self._do_queries(
            datetime.date(self.curr_year, 3, 1),
            datetime.date(self.curr_year, 3, 31))
        variation = self._eval_by_account_id('balp[]')
        self.assertEquals(variation, {
            self.account_ar.id: 500,
            self.account_in.id: -500,
        })
        variation = self._eval_by_account_id('balp[700IN]')
        self.assertEquals(variation, {
            self.account_in.id: -500,
        })
        end = self._eval_by_account_id('bale[]')
        self.assertEquals(end, {
            self.account_ar.id: 900,
            self.account_in.id: -800,
        })

    def test_aep_convenience_methods(self):
        initial = AEP.get_balances_initial(
            self.company,
            time.strftime('%Y') + '-03-01',
            'posted')
        self.assertEquals(initial, {
            self.account_ar.id: (400, 0),
            self.account_in.id: (0, 300),
        })
        variation = AEP.get_balances_variation(
            self.company,
            time.strftime('%Y') + '-03-01',
            time.strftime('%Y') + '-03-31',
            'posted')
        self.assertEquals(variation, {
            self.account_ar.id: (500, 0),
            self.account_in.id: (0, 500),
        })
        end = AEP.get_balances_end(
            self.company,
            time.strftime('%Y') + '-03-31',
            'posted')
        self.assertEquals(end, {
            self.account_ar.id: (900, 0),
            self.account_in.id: (0, 800),
        })
        unallocated = AEP.get_unallocated_pl(
            self.company,
            time.strftime('%Y') + '-03-15',
            'posted')
        self.assertEquals(unallocated, (0, 100))
