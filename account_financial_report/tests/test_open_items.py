# Author: Julien Coux
# Copyright 2016 Camptocamp SA
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

    def test_partner_filter(self):
        partner_1 = self.env.ref("base.res_partner_1")
        partner_2 = self.env.ref("base.res_partner_2")
        partner_3 = self.env.ref("base.res_partner_3")
        partner_4 = self.env.ref("base.res_partner_4")
        partner_1.write({"is_company": False, "parent_id": partner_2.id})
        partner_3.write({"is_company": False})

        expected_list = [partner_2.id, partner_3.id, partner_4.id]
        context = {
            "active_ids": [partner_1.id, partner_2.id, partner_3.id, partner_4.id],
            "active_model": "res.partner",
        }

        wizard = self.env["open.items.report.wizard"].with_context(**context)
        self.assertEqual(wizard._default_partners(), expected_list)

    def test_all_accounts_loaded(self):
        # Tests if all accounts are loaded when the account_code_ fields changed
        all_accounts = self.env["account.account"].search(
            [("reconcile", "=", True)], order="code"
        )
        open_items = self.env["open.items.report.wizard"].create(
            {
                "account_code_from": self.account001.id,
                "account_code_to": all_accounts[-1].id,
            }
        )
        open_items.on_change_account_range()
        all_accounts_code_set = set()
        open_items_code_set = set()
        [all_accounts_code_set.add(account.code) for account in all_accounts]
        [open_items_code_set.add(account.code) for account in open_items.account_ids]
        self.assertEqual(len(open_items_code_set), len(all_accounts_code_set))
        self.assertTrue(open_items_code_set == all_accounts_code_set)

    def test_open_items_grouped_by(self):
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
                "grouped_by": "salesperson",
            }
        )
        wizard.on_change_account_range()
        res = wizard._prepare_report_open_items()
        self.assertEqual(res["grouped_by"], wizard.grouped_by)
