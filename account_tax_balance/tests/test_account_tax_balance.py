# Copyright 2016 Lorenzo Battistini - Agile Business Group
# Copyright 2016 Giovanni Capalbo <giovanni@therp.nl>
# Copyright 2019 Andrea Stirpe <a.stirpe@onestein.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from dateutil.rrule import MONTHLY

import odoo
from odoo.fields import Date
from odoo.tests.common import HttpCase


@odoo.tests.tagged("post_install", "-at_install")
class TestAccountTaxBalance(HttpCase):
    def setUp(self):
        super().setUp()

        self.company = self.env.user.company_id
        self.range_type = self.env["date.range.type"].create(
            {"name": "Fiscal year", "allow_overlap": False}
        )
        self.range_generator = self.env["date.range.generator"]
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        range_generator = self.range_generator.create(
            {
                "date_start": "%s-01-01" % self.current_year,
                "name_prefix": "%s-" % self.current_year,
                "type_id": self.range_type.id,
                "duration_count": 1,
                "unit_of_time": str(MONTHLY),
                "count": 12,
            }
        )
        range_generator.action_apply()
        self.range = self.env["date.range"]

    def test_tax_balance(self):
        previous_taxes_ids = (
            self.env["account.tax"].search([("has_moves", "=", True)]).ids
        )
        tax_account_id = (
            self.env["account.account"]
            .create(
                {
                    "name": "Tax Paid",
                    "code": "TAXTEST",
                    "user_type_id": self.env.ref(
                        "account.data_account_type_current_liabilities"
                    ).id,
                }
            )
            .id
        )
        tax = self.env["account.tax"].create(
            {"name": "Tax 10.0%", "amount": 10.0, "amount_type": "percent"}
        )
        invoice_line_account_id = (
            self.env["account.account"]
            .create(
                {
                    "user_type_id": self.env.ref(
                        "account.data_account_type_expenses"
                    ).id,
                    "code": "EXPTEST",
                    "name": "Test expense account",
                }
            )
            .id
        )
        product = self.env.ref("product.product_product_4")
        invoice = self.env["account.move"].create(
            {
                "partner_id": self.env.ref("base.res_partner_2").id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        None,
                        {
                            "product_id": product.id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "name": "product that cost 100",
                            "account_id": invoice_line_account_id,
                            "tax_ids": [(6, 0, [tax.id])],
                        },
                    )
                ],
            }
        )

        invoice._onchange_invoice_line_ids()
        invoice._convert_to_write(invoice._cache)
        self.assertEqual(invoice.state, "draft")

        # change the state of invoice to open by clicking Validate button
        invoice.action_post()

        self.assertEqual(tax.base_balance, 100.0)
        self.assertEqual(tax.balance, 10.0)
        self.assertEqual(tax.base_balance_regular, 100.0)
        self.assertEqual(tax.balance_regular, 10.0)
        self.assertEqual(tax.base_balance_refund, 0.0)
        self.assertEqual(tax.balance_refund, 0.0)

        # testing wizard
        current_range = self.range.search(
            [
                (
                    "date_start",
                    "=",
                    "{}-{}-01".format(self.current_year, self.current_month),
                )
            ]
        )
        wizard = self.env["wizard.open.tax.balances"].new({})
        self.assertFalse(wizard.from_date)
        self.assertFalse(wizard.to_date)
        wizard = self.env["wizard.open.tax.balances"].new(
            {"date_range_id": current_range[0].id}
        )
        self.assertEqual(wizard.from_date, current_range[0].date_start)
        self.assertEqual(wizard.to_date, current_range[0].date_end)
        action = wizard.open_taxes()
        self.assertEqual(action["context"]["from_date"], current_range[0].date_start)
        self.assertEqual(action["context"]["to_date"], current_range[0].date_end)

        # exercise search has_moves = True
        taxes = self.env["account.tax"].search(
            [("has_moves", "=", True), ("id", "not in", previous_taxes_ids)]
        )
        self.assertEqual(len(taxes), 1)
        self.assertEqual(taxes[0].name, "Tax 10.0%")

        # testing buttons
        tax_action = tax.view_tax_lines()
        base_action = tax.view_base_lines()
        tax_action_move_lines = self.env["account.move.line"].search(
            tax_action["domain"]
        )
        self.assertTrue(invoice.line_ids & tax_action_move_lines)
        self.assertEqual(tax_action["xml_id"], "account.action_account_moves_all_tree")
        base_action_move_lines = self.env["account.move.line"].search(
            base_action["domain"]
        )
        self.assertTrue(invoice.line_ids & base_action_move_lines)
        self.assertEqual(base_action["xml_id"], "account.action_account_moves_all_tree")

        # test specific method
        state_list = tax.get_target_state_list(target_move="all")
        self.assertEqual(state_list, ["posted", "draft"])
        state_list = tax.get_target_state_list(target_move="whatever")
        self.assertEqual(state_list, [])

        product = self.env.ref("product.product_product_2")
        refund = self.env["account.move"].create(
            {
                "partner_id": self.env.ref("base.res_partner_2").id,
                "move_type": "out_refund",
                "invoice_line_ids": [
                    (
                        0,
                        None,
                        {
                            "product_id": product.id,
                            "quantity": 1.0,
                            "price_unit": 25.0,
                            "name": "returned product that cost 25",
                            "account_id": invoice_line_account_id,
                            "tax_ids": [(6, 0, [tax.id])],
                        },
                    )
                ],
            }
        )

        refund._onchange_invoice_line_ids()
        refund._convert_to_write(invoice._cache)
        self.assertEqual(refund.state, "draft")

        # change the state of refund to open by clicking Validate button
        refund.action_post()

        # force the _compute_balance() to be triggered
        tax._compute_balance()

        self.assertEqual(tax.base_balance, 75.0)
        self.assertEqual(tax.balance, 7.5)
        self.assertEqual(tax.base_balance_regular, 100.0)
        self.assertEqual(tax.balance_regular, 10.0)
        self.assertEqual(tax.base_balance_refund, -25.0)
        self.assertEqual(tax.balance_refund, -2.5)

        # Taxes on liquidity type moves are included
        tax_repartition_line = tax.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )
        liquidity_account_id = (
            self.env["account.account"]
            .search(
                [
                    ("internal_type", "=", "liquidity"),
                    ("company_id", "=", self.company.id),
                ],
                limit=1,
            )
            .id
        )
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": Date.context_today(self.env.user),
                "journal_id": self.env["account.journal"]
                .search(
                    [("type", "=", "bank"), ("company_id", "=", self.company.id)],
                    limit=1,
                )
                .id,
                "name": "Test move",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": liquidity_account_id,
                            "debit": 110,
                            "credit": 0,
                            "name": "Bank Fees",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": invoice_line_account_id,
                            "debit": 0,
                            "credit": 100,
                            "name": "Bank Fees",
                            "tax_ids": [(4, tax.id)],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": tax_account_id,
                            "debit": 0,
                            "credit": 10,
                            "name": "Bank Fees",
                            "tax_repartition_line_id": tax_repartition_line.id,
                        },
                    ),
                ],
            }
        )
        move.action_post()
        tax.refresh()
        self.assertEqual(tax.base_balance, 175.0)
        self.assertEqual(tax.balance, 17.5)
