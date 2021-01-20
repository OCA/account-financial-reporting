# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group
# © 2016 Giovanni Capalbo <giovanni@therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.fields import Date
from openerp.tests.common import TransactionCase
from datetime import datetime
from dateutil.rrule import MONTHLY


class TestAccountTaxBalance(TransactionCase):

    def setUp(self):
        super(TestAccountTaxBalance, self).setUp()
        self.range_type = self.env['date.range.type'].create(
            {'name': 'Fiscal year',
             'company_id': False,
             'allow_overlap': False})
        self.range_generator = self.env['date.range.generator']
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        range_generator = self.range_generator.create({
            'date_start': '%s-01-01' % self.current_year,
            'name_prefix': '%s-' % self.current_year,
            'type_id': self.range_type.id,
            'duration_count': 1,
            'unit_of_time': MONTHLY,
            'count': 12})
        range_generator.action_apply()
        self.range = self.env['date.range']

    def test_tax_balance(self):
        tax_account_id = self.env['account.account'].search(
            [('name', '=', 'Tax Paid')], limit=1).id
        tax = self.env['account.tax'].create({
            'name': 'Tax 10.0%',
            'amount': 10.0,
            'amount_type': 'percent',
            'account_id': tax_account_id,
        })
        invoice_account_id = self.env['account.account'].search(
            [('user_type_id', '=', self.env.ref(
                'account.data_account_type_receivable'
            ).id)], limit=1).id
        invoice_line_account_id = self.env['account.account'].search(
            [('user_type_id', '=', self.env.ref(
                'account.data_account_type_expenses').id)], limit=1).id
        invoice = self.env['account.invoice'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'account_id': invoice_account_id,
            'type': 'out_invoice',
        })

        self.env['account.invoice.line'].create({
            'product_id': self.env.ref('product.product_product_4').id,
            'quantity': 1.0,
            'price_unit': 100.0,
            'invoice_id': invoice.id,
            'name': 'product that cost 100',
            'account_id': invoice_line_account_id,
            'invoice_line_tax_ids': [(6, 0, [tax.id])],
        })
        invoice._onchange_invoice_line_ids()
        invoice._convert_to_write(invoice._cache)
        self.assertEqual(invoice.state, 'draft')

        # change the state of invoice to open by clicking Validate button
        invoice.action_invoice_open()

        self.assertEquals(tax.base_balance, 100.)
        self.assertEquals(tax.balance, 10.)
        self.assertEquals(tax.base_balance_regular, 100.)
        self.assertEquals(tax.balance_regular, 10.)
        self.assertEquals(tax.base_balance_refund, 0.)
        self.assertEquals(tax.balance_refund, 0.)

        # testing wizard
        current_range = self.range.search([
            ('date_start', '=', '%s-%s-01' % (
                self.current_year, self.current_month))
        ])
        wizard = self.env['wizard.open.tax.balances'].new({})
        self.assertFalse(wizard.from_date)
        self.assertFalse(wizard.to_date)
        wizard = self.env['wizard.open.tax.balances'].new({
            'date_range_id': current_range[0].id,
        })
        wizard.onchange_date_range_id()
        wizard._convert_to_write(wizard._cache)
        action = wizard.open_taxes()
        self.assertEqual(
            action['context']['from_date'], current_range[0].date_start)
        self.assertEqual(
            action['context']['to_date'], current_range[0].date_end)
        self.assertEqual(
            action['xml_id'], 'account_tax_balance.action_tax_balances_tree')

        # exercise search has_moves = True
        taxes = self.env['account.tax'].search([('has_moves', '=', True)])
        self.assertIn(tax, taxes)

        # testing buttons
        tax_action = tax.view_tax_lines()
        base_action = tax.view_base_lines()
        tax_action_move_lines = self.env['account.move.line'].\
            search(tax_action['domain'])
        self.assertTrue(invoice.move_id.line_ids & tax_action_move_lines)
        self.assertEqual(
            tax_action['xml_id'], 'account.action_account_moves_all_tree')
        base_action_move_lines = self.env['account.move.line'].\
            search(base_action['domain'])
        self.assertTrue(invoice.move_id.line_ids & base_action_move_lines)
        self.assertEqual(
            base_action['xml_id'], 'account.action_account_moves_all_tree')

        # test specific method
        state_list = tax.get_target_state_list(target_move='all')
        self.assertEqual(state_list, ['posted', 'draft'])
        state_list = tax.get_target_state_list(target_move='whatever')
        self.assertEqual(state_list, [])

        refund = self.env['account.invoice'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'account_id': invoice_account_id,
            'type': 'out_refund',
        })

        self.env['account.invoice.line'].create({
            'product_id': self.env.ref('product.product_product_2').id,
            'quantity': 1.0,
            'price_unit': 25.0,
            'invoice_id': refund.id,
            'name': 'returned product that cost 25',
            'account_id': invoice_line_account_id,
            'invoice_line_tax_ids': [(6, 0, [tax.id])],
        })
        refund._onchange_invoice_line_ids()
        refund._convert_to_write(invoice._cache)
        self.assertEqual(refund.state, 'draft')

        # change the state of refund to open by clicking Validate button
        refund.action_invoice_open()

        self.assertEquals(tax.base_balance, 75.)
        self.assertEquals(tax.balance, 7.5)
        self.assertEquals(tax.base_balance_regular, 100.)
        self.assertEquals(tax.balance_regular, 10.)
        self.assertEquals(tax.base_balance_refund, -25.)
        self.assertEquals(tax.balance_refund, -2.5)

        # Taxes on liquidity type moves are included
        liquidity_account_id = self.env['account.account'].search(
            [('internal_type', '=', 'liquidity')], limit=1).id
        self.env['account.move'].create({
            'date': Date.context_today(self.env.user),
            'journal_id': self.env['account.journal'].search(
                [('type', '=', 'bank')], limit=1).id,
            'name': 'Test move',
            'line_ids': [(0, 0, {
                'account_id': liquidity_account_id,
                'debit': 110,
                'credit': 0,
                'name': 'Bank Fees',
            }), (0, 0, {
                'account_id': invoice_line_account_id,
                'debit': 0,
                'credit': 100,
                'name': 'Bank Fees',
                'tax_ids': [(4, tax.id)]
            }), (0, 0, {
                'account_id': tax.account_id.id,
                'debit': 0,
                'credit': 10,
                'name': 'Bank Fees',
                'tax_line_id': tax.id,
            })],
        }).post()
        tax.refresh()
        self.assertEquals(tax.base_balance, 175.)
        self.assertEquals(tax.balance, 17.5)

    def test_receivable_move_type(self):
        """
        Receivable moves linked to invoices are not considered as refunds.
        Also, receivable moves coming from refunds are considered as such.
        """
        receivable_account = self.env['account.account'].search(
            [('user_type_id', '=', self.env.ref(
                'account.data_account_type_receivable'
            ).id)], limit=1)
        invoice = self.env['account.invoice'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'account_id': receivable_account.id,
            'type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.env.ref('product.product_product_4').id,
                'account_id': receivable_account.id,
                'quantity': 1.0,
                'price_unit': 100.0,
                'name': 'product that costs 100',
            }), (0, 0, {
                'product_id': self.env.ref('product.product_product_4').id,
                'account_id': receivable_account.id,
                'quantity': 1.0,
                'price_unit': -100.0,
                'name': 'product that costs -100',
            })]
        })
        invoice.action_invoice_open()
        self.assertEqual(invoice.move_id.move_type, 'receivable')

        refund = invoice.refund()
        refund.action_invoice_open()
        self.assertEqual(refund.move_id.move_type, 'receivable_refund')

    def test_payable_move_type(self):
        """
        Payable moves linked to bills are not considered as refunds.
        Also, payable moves coming from refunds are considered as such.
        """
        payable_account = self.env['account.account'].search(
            [('user_type_id', '=', self.env.ref(
                'account.data_account_type_payable'
            ).id)], limit=1)
        bill = self.env['account.invoice'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'account_id': payable_account.id,
            'type': 'in_invoice',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.env.ref('product.product_product_4').id,
                'account_id': payable_account.id,
                'quantity': 1.0,
                'price_unit': 100.0,
                'name': 'product that costs 100',
            }), (0, 0, {
                'product_id': self.env.ref('product.product_product_4').id,
                'account_id': payable_account.id,
                'quantity': 1.0,
                'price_unit': -100.0,
                'name': 'product that costs -100',
            })]
        })
        bill.action_invoice_open()
        self.assertEqual(bill.move_id.move_type, 'payable')

        refund = bill.refund()
        refund.action_invoice_open()
        self.assertEqual(refund.move_id.move_type, 'payable_refund')
