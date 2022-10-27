# Copyright 2016 Lorenzo Battistini - Agile Business Group
# Copyright 2016 Giovanni Capalbo <giovanni@therp.nl>
# Copyright 2019 Andrea Stirpe <a.stirpe@onestein.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from dateutil.rrule import MONTHLY

import odoo
from odoo import fields
from odoo.fields import Date
from odoo.tests.common import Form, HttpCase

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@odoo.tests.tagged("post_install", "-at_install")
class TestAccountTaxBalance(HttpCase):
    def setUp(self):
        super().setUp()
        self.env.user.groups_id = [(4, self.env.ref("account.group_account_user").id)]
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
        tax_account_id = self.env["account.account"].create(
            {
                "name": "Tax Paid",
                "code": "TAXTEST",
                "account_type": "liability_current",
            }
        )
        tax = self.env["account.tax"].create(
            {"name": "Tax 10.0%", "amount": 10.0, "amount_type": "percent"}
        )
        invoice_line_account_id = self.env["account.account"].create(
            {
                "account_type": "expense",
                "code": "EXPTEST",
                "name": "Test expense account",
            }
        )
        product = self.env.ref("product.product_product_4")
        invoice_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_invoice",
            )
        )
        invoice_form.partner_id = self.env.ref("base.res_partner_2")
        with invoice_form.invoice_line_ids.new() as line:
            line.product_id = product
            line.quantity = 1.0
            line.price_unit = 100.0
            line.name = "product that cost 100"
            line.account_id = invoice_line_account_id
            line.tax_ids.clear()
            line.tax_ids.add(tax)
        invoice = invoice_form.save()

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
        with Form(
            self.env["account.move"].with_context(default_move_type="out_refund")
        ) as refund_form:
            refund_form.partner_id = self.env.ref("base.res_partner_2")
            with refund_form.invoice_line_ids.new() as line:
                line.product_id = product
                line.quantity = 1.0
                line.price_unit = 25.0
                line.name = "returned product that cost 25"
                line.account_id = invoice_line_account_id
                line.tax_ids.clear()
                line.tax_ids.add(tax)

            refund = refund_form.save()

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
        liquidity_account_id = self.env["account.account"].search(
            [
                ("account_type", "in", ["asset_cash", "liability_credit_card"]),
                ("company_id", "=", self.company.id),
            ],
            limit=1,
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
                            "account_id": liquidity_account_id.id,
                            "debit": 110,
                            "credit": 0,
                            "name": "Bank Fees",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": invoice_line_account_id.id,
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
                            "account_id": tax_account_id.id,
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
        tax.invalidate_recordset()
        self.assertEqual(tax.base_balance, 175.0)
        self.assertEqual(tax.balance, 17.5)


@odoo.tests.tagged("post_install", "-at_install")
class TestInvoicingBalance(AccountTestInvoicingCommon):
    def test_balance_recomputation(self):
        """Check that balances are computed correctly for different dates."""
        partner = self.partner_a
        tax = self.tax_sale_a
        today = fields.Date.today()
        self.init_invoice(
            "in_invoice",
            partner=partner,
            invoice_date=today,
            post=True,
            amounts=[100],
            taxes=tax,
        )
        tomorrow = today + timedelta(days=1)
        self.init_invoice(
            "in_invoice",
            partner=partner,
            invoice_date=tomorrow,
            post=True,
            amounts=[200],
            taxes=tax,
        )

        # Check today's balance
        self.check_date_balance(tax, today, -15)

        # Check tomorrow's balance
        self.check_date_balance(tax, tomorrow, -30)

    def check_date_balance(self, tax, date, balance):
        """Compare expected balance with tax's balance in specified date."""
        tax = tax.with_context(
            from_date=date,
            to_date=date,
        )
        self.assertEqual(tax.balance, balance)
