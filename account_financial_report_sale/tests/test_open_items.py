# Copyright 2024 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.fields import Date
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestOpenItems(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.account001 = cls.env["account.account"].create(
            {
                "code": "001",
                "name": "Account 001",
                "account_type": "income_other",
                "reconcile": True,
            }
        )

    def test_open_items_grouped_by_partner_shipping(self):
        open_item_wizard = self.env["open.items.report.wizard"]
        all_accounts = self.env["account.account"].search(
            [
                ("reconcile", "=", True),
            ],
            order="code",
        )
        wizard = open_item_wizard.create(
            {
                "date_at": Date.today(),
                "account_code_from": self.account001.id,
                "account_code_to": all_accounts[-1].id,
                "grouped_by": "partner_shipping",
            }
        )
        wizard.on_change_account_range()
        res = wizard._prepare_report_open_items()
        self.assertEqual(res["grouped_by"], wizard.grouped_by)
