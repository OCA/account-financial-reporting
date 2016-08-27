# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp import fields
from openerp.tests import common
to_string = fields.Date.to_string


class TestAccountMoveLine(common.TransactionCase):

    def setUp(self):
        super(TestAccountMoveLine, self).setUp()

        self.date_1 = datetime.now()
        self.date_2 = datetime.now() + relativedelta(days=1)

        self.account_expense = self.env['account.account'].search([
            ('type', '=', 'other'),
        ], limit=1)

        self.account_receivable = self.env['account.account'].search([
            ('type', '=', 'receivable'),
        ], limit=1)

        self.journal = self.env['account.journal'].search([
            ('type', '=', 'bank'),
        ], limit=1)

        self.period_1 = self.env['account.period'].find(self.date_1)
        self.period_2 = self.env['account.period'].find(self.date_2)

        self.move_1 = self.env['account.move'].create({
            'name': '/',
            'journal_id': self.journal.id,
            'date': self.date_1,
            'period_id': self.period_1.id,
            'line_id': [
                (0, 0, {
                    'name': '/',
                    'account_id': self.account_receivable.id,
                    'debit': 100,
                }),
                (0, 0, {
                    'name': '/',
                    'account_id': self.account_expense.id,
                    'credit': 100,
                }),
            ]
        })

        self.line_1 = self.move_1.line_id.sorted(lambda l: l.id)[0]

    def create_payment_move(self, amount):
        return self.env['account.move'].create({
            'name': '/',
            'journal_id': self.journal.id,
            'date': self.date_2,
            'period_id': self.period_2.id,
            'line_id': [
                (0, 0, {
                    'name': '/',
                    'account_id': self.account_receivable.id,
                    'credit': amount,
                }),
                (0, 0, {
                    'name': '/',
                    'account_id': self.account_expense.id,
                    'debit': amount,
                }),
            ]
        })

    def test_01_last_rec_date(self):
        self.move_2 = self.create_payment_move(100)
        self.line_2 = self.move_2.line_id.sorted(lambda l: l.id)[0]

        self.reconcile = self.env['account.move.reconcile'].create({
            'name': 'A999',
            'type': 'auto',
            'line_id': [(4, self.line_1.id), (4, self.line_2.id)]
        })
        self.assertEqual(self.line_1.last_rec_date, to_string(self.date_2))

    def test_02_last_rec_date_with_partial_reconcile(self):
        self.move_2 = self.create_payment_move(50)
        self.line_2 = self.move_2.line_id.sorted(lambda l: l.id)[0]

        self.move_3 = self.create_payment_move(50)
        self.line_3 = self.move_3.line_id.sorted(lambda l: l.id)[0]

        self.reconcile = self.env['account.move.reconcile'].create({
            'name': 'A999',
            'type': 'auto',
            'line_partial_ids': [
                (4, self.line_1.id), (4, self.line_2.id), (4, self.line_3.id)
            ]
        })
        self.assertEqual(self.line_1.last_rec_date, to_string(self.date_2))
