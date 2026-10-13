# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingHttpCommon


@tagged("post_install", "-at_install")
class TestAccountTaxBalanceTour(AccountTestInvoicingHttpCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        today = fields.Date.today()
        cls.env["date.range"].create(
            {
                "name": "Tour range",
                "date_start": today.replace(month=1, day=1),
                "date_end": today.replace(month=12, day=31),
                "type_id": cls.env["date.range.type"].create({"name": "Tour type"}).id,
            }
        )
        invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner_a.id,
                "invoice_date": today,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Tour line",
                            "quantity": 1,
                            "price_unit": 100,
                            "tax_ids": [
                                Command.set(cls.company_data["default_tax_sale"].ids)
                            ],
                        }
                    )
                ],
            }
        )
        invoice.action_post()
        cls.env.flush_all()

    def test_open_taxes_tour(self):
        self.start_tour(
            "/odoo/action-account_tax_balance.action_open_tax_balances",
            "account_tax_balance_open_taxes",
            login=self.env.user.login,
        )
