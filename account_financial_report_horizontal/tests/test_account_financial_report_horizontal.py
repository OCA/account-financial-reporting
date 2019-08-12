# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from lxml import etree
from odoo.tests.common import TransactionCase


class TestAccountFinancialReportHorizontal(TransactionCase):
    def test_account_financial_report_horizontal(self):
        action = self.env['accounting.report'].with_context(
            active_id=self.env.ref('account.menu_account_report_pl').id,
            active_model='ir.ui.view',
        ).create({}).check_report()
        data = action['data']
        report = self.env['ir.actions.report']._get_report_from_name(
            action['report_name'])
        html = report.with_context(action['context']).render_qweb_html(
            self.env[data['model']].browse(data['ids']),
            data=data,
        )[0]
        self.assertTrue(etree.fromstring(html).xpath("//div[hasclass('row')]"))
