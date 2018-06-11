# -*- coding: utf-8 -*-
# Copyright  2018 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from . import abstract_test

_logger = logging.getLogger(__name__)


class AbstractTestForeignCurrency(abstract_test.AbstractTest):
    """Common technical tests for all reports."""

    def _chart_template_create(self):
        super(AbstractTestForeignCurrency, self)._chart_template_create()
        # Account for foreign payments
        self.account_type_other = self.env['account.account.type'].create(
            {'name': 'foreign expenses',
             'type': 'other',
             })
        act = self.env['account.account.template'].create({
            'code': '0012',
            'name': 'Foreign Expenses',
            'user_type_id': self.account_type_other.id,
            'chart_template_id': self.chart.id,
            'currency_id': self.env.ref('base.EUR').id,
        })
        self.env['ir.model.data'].create({
            'res_id': act.id,
            'model': act._name,
            'name': 'foreign expenses',
        })
        return True

    def _add_chart_of_accounts(self):
        super(AbstractTestForeignCurrency, self)._add_chart_of_accounts()
        self.foreign_expense = self.env['account.account'].search(
            [('currency_id', '=', self.env.ref('base.EUR').id)], limit=1)
        self.foreign_currency_id = self.foreign_expense.currency_id
        return True

    def _journals_create(self):
        super(AbstractTestForeignCurrency, self)._journals_create()
        self.journal_foreign_purchases = self.env['account.journal'].create({
            'company_id': self.company.id,
            'name': 'Test journal for purchase',
            'type': 'purchase',
            'code': 'TFORPUR',
            'default_debit_account_id': self.foreign_expense.id,
            'default_credit_account_id': self.foreign_expense.id,
            'currency_id': self.foreign_currency_id.id,
        })
        return True

    def _invoice_create(self):
        super(AbstractTestForeignCurrency, self)._invoice_create()
        # vendor bill foreign currency
        foreign_vendor_invoice_lines = [(0, False, {
            'name': 'Test description #1',
            'account_id': self.revenue.id,
            'quantity': 1.0,
            'price_unit': 100.0,
            'currency_id': self.foreign_currency_id.id,
        }), (0, False, {
            'name': 'Test description #2',
            'account_id': self.revenue.id,
            'quantity': 2.0,
            'price_unit': 25.0,
            'currency_id': self.foreign_currency_id.id,
        })]
        self.foreign_invoice_in = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'in_invoice',
            'invoice_line_ids': foreign_vendor_invoice_lines,
            'account_id': self.partner.property_account_payable_id.id,
            'journal_id': self.journal_foreign_purchases.id,
        })
        self.foreign_invoice_in.action_invoice_open()
        return True
