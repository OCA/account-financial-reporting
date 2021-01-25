# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


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
