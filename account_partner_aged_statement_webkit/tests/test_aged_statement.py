# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Savoir-faire Linux. All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import netsvc
from datetime import datetime
from openerp.tests import common
from ..report.partner_aged_statement_report import PartnerAgedTrialReport
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

from dateutil.relativedelta import relativedelta


class test_aged_statement(common.TransactionCase):

    def create_fiscal_year(self, year):
        cr, uid, context = self.cr, self.uid, self.context

        fy_id = self.fiscal_year_model.create(cr, uid, {
            'name': 'Test %s' % year,
            'code': 'FY%s' % year,
            'company_id': self.company_id,
            'date_start': datetime(year, 1, 1),
            'date_stop': datetime(year, 12, 31),
        }, context=context)

        fy = self.fiscal_year_model.browse(cr, uid, fy_id, context=context)
        fy.create_period()

    def setUp(self):
        super(test_aged_statement, self).setUp()
        self.user_model = self.registry("res.users")
        self.partner_model = self.registry("res.partner")
        self.invoice_model = self.registry("account.invoice")
        self.account_model = self.registry("account.account")
        self.journal_model = self.registry("account.journal")
        self.company_model = self.registry("res.company")
        self.fiscal_year_model = self.registry("account.fiscalyear")

        self.context = self.user_model.context_get(self.cr, self.uid)

        cr, uid, context = self.cr, self.uid, self.context

        self.company_id = self.user_model.browse(
            cr, uid, uid, context=context).company_id.id

        self.partner_id = self.partner_model.create(
            cr, uid, {'name': 'Test', 'customer': True}, context=context)

        self.account_id = self.account_model.search(
            cr, uid, [
                ('type', '=', 'receivable'),
                ('currency_id', '=', False),
            ], context=context)[0]

        self.account_2_id = self.account_model.search(
            cr, uid, [
                ('type', '=', 'other'),
                ('currency_id', '=', False),
            ], context=context)[0]

        self.journal_id = self.journal_model.search(
            cr, uid, [('type', '=', 'sale')], context=context)[0]

        self.today = datetime.now()

        self.create_fiscal_year(self.today.year - 1)

        self.date1 = self.today - relativedelta(weeks=2)
        self.date2 = self.today - relativedelta(months=1, weeks=1)
        self.date3 = self.today - relativedelta(months=2, weeks=1)
        self.date4 = self.today - relativedelta(months=3, weeks=1)
        self.date5 = self.today - relativedelta(months=4, weeks=1)

        self.invoice_ids = [
            self.invoice_model.create(
                cr, uid, {
                    'journal_id': self.journal_id,
                    'account_id': self.account_id,
                    'partner_id': self.partner_id,
                    'date_invoice': invoice[0],
                    'invoice_line': [(0, 0, {
                        'name': 'Test',
                        'account_id': self.account_2_id,
                        'price_unit': invoice[1],
                        'quantity': 1,
                    })],
                }, context=context)
            for invoice in [
                (self.today, 300),
                (self.date1, 100),
                (self.date2, 150),
                (self.date3, 200),
                (self.date4, 250),
                (self.date5, 500),
            ]
        ]

        wf_service = netsvc.LocalService("workflow")
        for inv_id in self.invoice_ids:
            wf_service.trg_validate(
                uid, 'account.invoice', inv_id, 'invoice_open', cr)

        self.report = PartnerAgedTrialReport(
            cr, uid, 'webkit.partner_aged_statement_report',
            context=context)

        self.partner = self.partner_model.browse(
            cr, uid, self.partner_id, context=context)

        self.company = self.company_model.browse(
            cr, uid, self.company_id, context=context)

    def test_get_balance(self):
        balance = self.report._get_balance(self.partner, self.company)

        self.assertEqual(len(balance), 1)
        self.assertEqual(balance[0]['30'], 400)
        self.assertEqual(balance[0]['3060'], 150)
        self.assertEqual(balance[0]['6090'], 200)
        self.assertEqual(balance[0]['90120'], 250)
        self.assertEqual(balance[0]['120'], 500)
        self.assertEqual(balance[0]['total'], 400 + 150 + 200 + 250 + 500)

    def compare_vals(self, line, vals):
        self.assertEqual(
            line['date_original'], vals['date_original'].strftime(
                DEFAULT_SERVER_DATE_FORMAT))
        self.assertEqual(line['amount_original'], vals['amount_original'])
        self.assertEqual(
            line['amount_unreconciled'], vals['amount_unreconciled'])

    def test_line_get_30(self):
        lines = sorted(
            self.report._lines_get_30(self.partner, self.company),
            key=lambda l: l['date_original'])

        self.compare_vals(lines[0], {
            'date_original': self.date1,
            'amount_original': 100,
            'amount_unreconciled': 100,
        })

        self.compare_vals(lines[1], {
            'date_original': self.today,
            'amount_original': 300,
            'amount_unreconciled': 300,
        })

    def test_line_get_30_60(self):
        lines = sorted(
            self.report._lines_get_30_60(self.partner, self.company),
            key=lambda l: l['date_original'])

        self.compare_vals(lines[0], {
            'date_original': self.date2,
            'amount_original': 150,
            'amount_unreconciled': 150,
        })

    def test_line_get_60(self):
        lines = sorted(
            self.report._lines_get_60(self.partner, self.company),
            key=lambda l: l['date_original'])

        self.compare_vals(lines[0], {
            'date_original': self.date5,
            'amount_original': 500,
            'amount_unreconciled': 500,
        })

        self.compare_vals(lines[1], {
            'date_original': self.date4,
            'amount_original': 250,
            'amount_unreconciled': 250,
        })

        self.compare_vals(lines[2], {
            'date_original': self.date3,
            'amount_original': 200,
            'amount_unreconciled': 200,
        })
