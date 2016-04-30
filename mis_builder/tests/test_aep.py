# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import datetime

from openerp import fields
import openerp.tests.common as common
from openerp.tools.safe_eval import safe_eval

from ..models.aep import AccountingExpressionProcessor as AEP
from ..models.accounting_none import AccountingNone


class TestAEP(common.TransactionCase):

    def setUp(self):
        super(TestAEP, self).setUp()
        self.account_model = self.env['account.account']
        self.move_model = self.env['account.move']
        self.journal_model = self.env['account.journal']
        self.curr_year = datetime.date.today().year
        self.prev_year = self.curr_year - 1
        # create receivable bs account
        type_ar = self.browse_ref('account.data_account_type_receivable')
        self.account_ar = self.account_model.create({
            'code': '400AR',
            'name': 'Receivable',
            'user_type_id': type_ar.id,
            'reconcile': True})
        # create income pl account
        type_in = self.browse_ref('account.data_account_type_revenue')
        self.account_in = self.account_model.create({
            'code': '700IN',
            'name': 'Income',
            'user_type_id': type_in.id})
        # create journal
        self.journal = self.journal_model.create({
            'name': 'Sale journal',
            'code': 'VEN',
            'type': 'sale'})
        # create the AEP, and prepare the expressions we'll need
        self.aep = AEP(self.env)
        self.aep.parse_expr("bali[]")
        self.aep.parse_expr("bale[]")
        self.aep.parse_expr("balp[]")
        self.aep.parse_expr("balu[]")
        self.aep.done_parsing(self.env.user.company_id)

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
                })
            ]})
        move.post()
        return move

    def _do_queries(self, date_from, date_to):
        self.aep.do_queries(
            date_from=fields.Date.to_string(date_from),
            date_to=fields.Date.to_string(date_to),
            target_move='posted',
            company=self.env.user.company_id
        )

    def _eval(self, expr, acc=None):
        eval_dict = {'AccountingNone': AccountingNone}
        if acc:
            return safe_eval(
                self.aep.replace_expr(expr, account_ids_filter=[acc.id]),
                eval_dict)
        else:
            return safe_eval(
                self.aep.replace_expr(expr),
                eval_dict)

    def test_sanity_check(self):
        self.assertEquals(self.env.user.company_id.fiscalyear_last_day, 31)
        self.assertEquals(self.env.user.company_id.fiscalyear_last_month, 12)

    def test_aep_1(self):
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

        # let's query for december
        self._do_queries(
            datetime.date(self.prev_year, 12, 1),
            datetime.date(self.prev_year, 12, 31))
        # initial balance must be None
        self.assertIs(self._eval('bali[]', self.account_in), AccountingNone)
        self.assertIs(self._eval('bali[]', self.account_ar), AccountingNone)
        # check variation
        self.assertEquals(self._eval('balp[]', self.account_in), -100)
        self.assertEquals(self._eval('balp[]', self.account_ar), 100)
        # check ending balance
        self.assertEquals(self._eval('bale[]', self.account_in), -100)
        self.assertEquals(self._eval('bale[]', self.account_ar), 100)

        # let's query for January
        self._do_queries(
            datetime.date(self.curr_year, 1, 1),
            datetime.date(self.curr_year, 1, 31))
        # initial balance is None for income account (it's not carried over)
        self.assertIs(self._eval('bali[]', self.account_in), AccountingNone)
        self.assertEquals(self._eval('bali[]', self.account_ar), 100)
        # check variation
        self.assertEquals(self._eval('balp[]', self.account_in), -300)
        self.assertEquals(self._eval('balp[]', self.account_ar), 300)
        # check ending balance
        self.assertEquals(self._eval('bale[]', self.account_in), -300)
        self.assertEquals(self._eval('bale[]', self.account_ar), 400)

        # let's query for March
        self._do_queries(
            datetime.date(self.curr_year, 3, 1),
            datetime.date(self.curr_year, 3, 31))
        # initial balance is the ending balance fo January
        self.assertEquals(self._eval('bali[]', self.account_in), -300)
        self.assertEquals(self._eval('bali[]', self.account_ar), 400)
        # check variation
        self.assertEquals(self._eval('balp[]', self.account_in), -500)
        self.assertEquals(self._eval('balp[]', self.account_ar), 500)
        # check ending balance
        self.assertEquals(self._eval('bale[]', self.account_in), -800)
        self.assertEquals(self._eval('bale[]', self.account_ar), 900)

        # unallocated p&l from previous year
        self.assertEquals(self._eval('balu[]'), -100)

        # TODO allocate profits, and then...
