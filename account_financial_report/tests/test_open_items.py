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
    def setUpClass(cls):
        super().setUpClass()
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
        res = wizard._prepare_report_data()
        self.assertEqual(res["grouped_by"], wizard.grouped_by)

    def test_branch_company(self):
        """Open items for a branch must include parent company accounts."""
        parent = self.env.company
        branch = self.env["res.company"].create(
            {"name": "Open Items Branch", "parent_id": parent.id}
        )
        parent_account = self.env["account.account"].search(
            [("company_ids", "in", [parent.id]), ("reconcile", "=", True)],
            limit=1,
        )
        self.assertTrue(parent_account)
        self.assertNotIn(branch, parent_account.company_ids)
        wizard = self.env["open.items.report.wizard"].create(
            {"date_at": Date.today(), "company_id": branch.id}
        )
        res = wizard.onchange_company_id()
        accounts_in_domain = self.env["account.account"].search(
            res["domain"]["account_ids"]
        )
        self.assertIn(parent_account, accounts_in_domain)
