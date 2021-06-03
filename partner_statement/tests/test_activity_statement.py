# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date
from odoo.tests.common import TransactionCase
from odoo import fields


class TestActivityStatement(TransactionCase):
    """
        Tests for Activity Statement.
    """
    def setUp(self):
        super().setUp()

        self.res_users_model = self.env['res.users']
        self.company = self.env.ref('base.main_company')
        self.partner1 = self.env.ref('base.res_partner_1')
        self.partner2 = self.env.ref('base.res_partner_2')
        self.g_account_user = self.env.ref('account.group_account_user')

        self.user = self._create_user('user_1', [self.g_account_user],
                                      self.company).id

        self.statement_model = \
            self.env['report.partner_statement.activity_statement']
        self.wiz = self.env['activity.statement.wizard']
        self.report_name = 'partner_statement.activity_statement'
        self.report_title = 'Activity Statement'
        self.today = fields.Date.context_today(self.wiz)

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

    def test_customer_activity_statement(self):

        wiz_id = self.wiz.with_context(
            active_ids=[self.partner1.id, self.partner2.id],
        ).create({})

        wiz_id.aging_type = 'months'
        wiz_id.show_aging_buckets = False

        statement = wiz_id.button_export_pdf()

        self.assertDictContainsSubset(
            {
                'type': 'ir.actions.report',
                'report_name': self.report_name,
                'report_type': 'qweb-pdf',
            },
            statement,
            'There was an error and the PDF report was not generated.'
        )

        data = wiz_id._prepare_statement()
        docids = data['partner_ids']
        report = self.statement_model._get_report_values(docids, data)
        self.assertIsInstance(report, dict,
                              "There was an error while compiling the report.")
        self.assertIn("bucket_labels", report,
                      "There was an error while compiling the report.")

    def test_customer_activity_report_no_wizard(self):
        docids = [self.partner1.id, self.partner2.id]
        report = self.statement_model._get_report_values(docids, False)
        self.assertIsInstance(report, dict,
                              "There was an error while compiling the report.")
        self.assertIn("bucket_labels", report,
                      "There was an error while compiling the report.")

    def test_date_formatting(self):
        date_fmt = '%d/%m/%Y'
        test_date = date(2018, 9, 30)
        res = self.statement_model._format_date_to_partner_lang(
            test_date, date_fmt
        )
        self.assertEqual(res, '30/09/2018')

        test_date_string = '2018-09-30'
        res = self.statement_model._format_date_to_partner_lang(
            test_date_string, date_fmt
        )
        self.assertEqual(res, '30/09/2018')

    def test_onchange_aging_type(self):
        """Test that partner data is filled accodingly"""
        wiz_id = self.wiz.with_context(
            active_ids=[self.partner1.id, self.partner2.id],
        ).new()
        wiz_id.aging_type = 'months'
        wiz_id.onchange_aging_type()
        self.assertEqual(wiz_id.date_end.month, wiz_id.date_start.month)
        self.assertTrue(wiz_id.date_end.day > wiz_id.date_start.day)
        self.assertTrue(wiz_id.date_end < self.today)

        wiz_id.aging_type = 'days'
        wiz_id.onchange_aging_type()
        self.assertEqual((wiz_id.date_end - wiz_id.date_start).days, 30)
        self.assertTrue(wiz_id.date_end == self.today)
