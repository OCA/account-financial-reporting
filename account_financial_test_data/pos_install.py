# -*- coding: utf-8 -*-
from openerp import SUPERUSER_ID, api, tools, _


def post_init_hook(cr, registry):

    def update_partners():
        """
        Set the right account on partners
        """

        partner_a = env.ref('account_financial_test_data.data_partner_a')
        partner_b = env.ref('account_financial_test_data.data_partner_b')
        partner_c = env.ref('account_financial_test_data.data_partner_c')
        partner_d = env.ref('account_financial_test_data.data_partner_d')
        partner_e = env.ref('account_financial_test_data.data_partner_e')
        partner_f = env.ref('account_financial_test_data.data_partner_f')
        partner_g = env.ref('account_financial_test_data.data_partner_g')

        account_a_receivable = env['account.account'].search(
            [('code', '=', '411700')]
        )

        account_receivable = env['account.account'].search(
            [('code', '=', '411100')]
        )

        account_payable = env['account.account'].search(
            [('code', '=', '401100')]
        )

        partner_a.property_account_receivable_id = account_a_receivable[0]
        partner_a.property_account_payable_id = account_payable[0]

        partners_list = [
            partner_b,
            partner_c,
            partner_d,
            partner_e,
            partner_f,
            partner_g
        ]

        for partner in partners_list:
            partner.property_account_receivable_id = account_receivable[0]
            partner.property_account_payable_id = account_payable[0]

        return True

    def update_account_settings():
        """
        Configure account settings
        """
        account_setting_obj = env['account.config.settings']
        account_setting = account_setting_obj.create({})
        account_setting.group_multi_currency = True
        account_setting.default_sale_tax_id = env.ref('l10n_fr.tva_normale').id
        account_setting.default_purchase_tax_id = env.ref('l10n_fr.tva_normale').id
        account_setting.execute()

        return True

    def update_account():
        """
        Change the name and currency of 411700
        """
        account_to_update = env['account.account'].search(
            [('code', '=', '411700')]
        )[0]
        account_to_update.name = "Clients - USD"
        account_to_update.currency_id = env.ref('base.USD').id

        return True

    def update_product():
        """
        Update the product with the right settings
        """
        product = env.ref('account_financial_test_data.data_product_a')
        product.standard_price = 1000
        product.lst_price = 1000
        product.taxes_id = [
            (6, 0, [env.ref('l10n_fr.tva_normale').id])
        ]

        product.supplier_taxes_id = [
            (6, 0, [env.ref('l10n_fr.tva_acq_normale_TTC').id])
        ]

        income_account = env['account.account'].search([
            ('code', '=', '707100')
        ])[0]
        expense_account = env['account.account'].search([
            ('code', '=', '607100')
        ])[0]

        product.property_account_income_id = income_account
        product.property_account_expense_id = expense_account

        return True

    def create_invoices():

        invoice_obj = env['account.invoice']
        invoice_line_obj = env['account.invoice.line']
        invoice_line_values = {

        }

        invoice_values = {
            'partner_id': env.ref(
                'account_financial_test_data.data_partner_c').id,
            'date_invoice': '05/01/2015',
            'user_id': env.ref('base.user_root').id,
            'currency_id': env.ref('base.EUR').id,
            'invoice_line_ids': [],

        }

        return True

    env = api.Environment(cr, SUPERUSER_ID, {})
    update_partners()
    update_account_settings()
    update_account()
    update_product()
    # create_invoices()
