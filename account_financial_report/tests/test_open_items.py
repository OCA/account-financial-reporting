# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, TransactionCase


class TestOpenItems(TransactionCase):
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

        wizard = self.env["open.items.report.wizard"].with_context(context)
        self.assertEqual(wizard._default_partners(), expected_list)

    def test_account_range_filter(self):
        account_cex001 = self.env["account.account"].create(
            {
                "code": "CEX001",
                "name": "Account CEX001",
                "user_type_id": self.env.ref(
                    "account.data_account_type_other_income"
                ).id,
                "reconcile": True,
            },
        )
        with Form(self.env["open.items.report.wizard"]) as wizard_form:
            wizard_form.account_code_from = account_cex001
            self.assertEqual([a for a in wizard_form.account_ids], [])
            wizard_form.account_code_to = account_cex001
            self.assertEqual(
                [a.id for a in wizard_form.account_ids], account_cex001.ids
            )
