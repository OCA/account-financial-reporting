# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group
# © 2016 Giovanni Capalbo <giovanni@therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase


class TestAccountTaxBalance(TransactionCase):

    def test_tax_balance(self):
        tax_account_id = self.env['account.account'].search(
            [('name', '=', 'Tax Paid')], limit=1).id
        tax = self.env['account.tax'].create({
            'name': 'Tax 10.0',
            'amount': 10.0,
            'amount_type': 'fixed',
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
        invoice.signal_workflow('invoice_open')

        self.assertEquals(tax.base_balance, -100)
        self.assertEquals(tax.balance, -10)
