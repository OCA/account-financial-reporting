# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date
from . import abstract_test_foreign_currency as a_t_f_c


class TestOpenItems(a_t_f_c.AbstractTestForeignCurrency):
    """
        Technical tests for Open Items Report.
    """

    def _getReportModel(self):
        return self.env['report_open_items']

    def _getQwebReportName(self):
        return 'account_financial_report.report_open_items_qweb'

    def _getXlsxReportName(self):
        return 'a_f_r.report_open_items_xlsx'

    def _getXlsxReportActionName(self):
        return 'account_financial_report.action_report_open_items_xlsx'

    def _getReportTitle(self):
        return 'Odoo'

    def _getBaseFilters(self):
        return {
            'date_at': date(date.today().year, 12, 31),
            'company_id': self.company.id,
            'foreign_currency': True,
        }

    def _getAdditionalFiltersToBeTested(self):
        return [
            {'only_posted_moves': True},
            {'hide_account_at_0': True},
            {'only_posted_moves': True, 'hide_account_at_0': True},
        ]

    def test_partner_filter(self):
        partner_1 = self.env.ref('base.res_partner_1')
        partner_2 = self.env.ref('base.res_partner_2')
        partner_3 = self.env.ref('base.res_partner_3')
        partner_4 = self.env.ref('base.res_partner_4')
        partner_1.write({'is_company': False,
                         'parent_id': partner_2.id})
        partner_3.write({'is_company': False})

        expected_list = [partner_2.id, partner_3.id, partner_4.id]
        context = {
            'active_ids': [
                partner_1.id, partner_2.id, partner_3.id, partner_4.id
                ],
            'active_model': 'res.partner'
            }

        wizard = self.env["open.items.report.wizard"].with_context(context)
        self.assertEqual(wizard._default_partners(), expected_list)
