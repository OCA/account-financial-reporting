#from openerp.addons.account.tests.account_test_users import AccountTestUsers
from openerp.tests.common import TransactionCase
from openerp.tools import float_compare
 

class TestAccountTaxBalance(TransactionCase):
    
    def setUp(self): 
        super(TestAccountTaxBalance, self).setUp() 
        self.fixed_tax = self.tax_model.create({
            'name': "Fixed tax",
            'amount_type': 'fixed',
            'amount': 10.0,
            'sequence': 1,
        })
        self.fixed_tax_bis = self.tax_model.create({
            'name': "Fixed tax bis",
            'amount_type': 'fixed',
            'amount': 15,
            'sequence': 2,
        })
        self.percent_tax = self.tax_model.create({
            'name': "Percent tax",
            'amount_type': 'percent',
            'amount': 10.0,
            'sequence': 3,
        })
        self.bank_journal = self.env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', self.account_manager.company_id.id)])[0]
        self.bank_account = self.bank_journal.default_debit_account_id
        self.expense_account = self.env['account.account'].search([('user_type_id.type', '=', 'payable')], limit=1) #Should be done by onchange later


    def test_tax_balance(self):
        company_id = self.env['res.users'].browse(self.env.uid).company_id.id
        tax = self.env['account.tax'].create({
            'name': 'Tax 10.0',
            'amount': 10.0,
            'amount_type': 'fixed',
        })
        analytic_account = self.env['account.analytic.account'].create({
            'name': 'test account',
        })
        invoice_account = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_receivable').id)], limit=1).id
        invoice_line_account = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_expenses').id)], limit=1).id
        invoice = self.env['account.invoice'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'account_id': invoice_account,
            'type': 'in_invoice',
        })

        self.env['account.invoice.line'].create({
            'product_id': self.env.ref('product.product_product_4').id,
            'quantity': 1.0,
            'price_unit': 100.0,
            'invoice_id': invoice.id,
            'name': 'product that cost 100',
            'account_id': invoice_line_account,
            'invoice_line_tax_ids': [(6, 0, [tax.id])],
            'account_analytic_id': analytic_account.id,
        })

        # :     check that Initially supplier bill state is "Draft"
        self.assertTrue((invoice.state == 'draft'), "Initially vendor bill state is Draft")

        #change the state of invoice to open by clicking Validate button
        invoice.signal_workflow('invoice_open')
       
        self.assertEquals(tax.base_balance, 100)
        self.assertEquals(tax.balance, 10)
        


