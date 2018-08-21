# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase


class TestCustomerOutstandingStatement(TransactionCase):
    """
        Tests for Customer Outstanding Statement.
    """
    def setUp(self):
        super(TestCustomerOutstandingStatement, self).setUp()

        self.res_users_model = self.env['res.users']
        self.company = self.env.ref('base.main_company')
        self.partner1 = self.env.ref('base.res_partner_1')
        self.partner2 = self.env.ref('base.res_partner_2')
        self.g_account_user = self.env.ref('account.group_account_user')

        self.user = self._create_user('user_1', [self.g_account_user],
                                      self.company).id

        self.statement_model = \
            self.env['report.customer_outstanding_statement.statement']
        self.wiz = self.env['customer.outstanding.statement.wizard']
        self.report_name = 'customer_outstanding_statement.statement'
        self.report_title = 'Customer Outstanding Statement'

    def _create_user(self, login, groups, company):
        group_ids = [group.id for group in groups]
        user = self.res_users_model.create({
            'name': login,
            'login': login,
            'password': 'demo',
            'email': 'example@yourcompany.com',
            'company_id': company.id,
            'company_ids': [(4, company.id)],
            'groups_id': [(6, 0, group_ids)]
        })
        return user

    def test_customer_outstanding_statement(self):

        wiz_id = self.wiz.with_context(
            active_ids=[self.partner1.id, self.partner2.id],
        ).create({})

        statement = wiz_id.button_export_pdf()

        self.assertDictContainsSubset(
            {
                'type': 'ir.actions.report.xml',
                'report_name': self.report_name,
                'report_type': 'qweb-pdf',
            },
            statement,
            'There was an error and the PDF report was not generated.'
        )

        data = wiz_id._prepare_outstanding_statement()
        report = self.statement_model.render_html(data)
        self.assertIsInstance(report, str,
                              "There was an error while compiling the report.")
        self.assertIn("<!DOCTYPE html>", report,
                      "There was an error while compiling the report.")
