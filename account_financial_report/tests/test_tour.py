# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingHttpCommon

ACTIONS = {
    "trial_balance_html": "action_trial_balance_wizard",
    "trial_balance_analytic_html": "action_trial_balance_wizard",
    "general_ledger_html": "action_general_ledger_wizard",
    "journal_ledger_html": "action_journal_ledger_wizard",
    "open_items_html": "action_open_items_wizard",
    "aged_partner_balance_html": "action_aged_partner_balance_wizard",
    "vat_report_html": "action_vat_report_wizard",
    "vat_report_taxgroups_html": "action_vat_report_wizard",
    "age_report_configuration": "action_aged_partner_report_configuration",
}


@tagged("post_install", "-at_install")
class TestReportTours(AccountTestInvoicingHttpCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_data["company"].external_report_layout_id = cls.env.ref(
            "web.external_layout_standard"
        )
        cls.env.user.group_ids |= cls.env.ref("analytic.group_analytic_accounting")
        today = fields.Date.today()
        cls.env["date.range"].create(
            {
                "name": "Tour range",
                "date_start": today.replace(month=1, day=1),
                "date_end": today.replace(month=12, day=31),
                "type_id": cls.env["date.range.type"].create({"name": "Tour type"}).id,
            }
        )
        receivable = cls.company_data["default_account_receivable"]
        receivable.parent_id = cls.env["account.account"].create(
            {"code": "1", "name": "Tour parent", "account_type": "income_other"}
        )
        analytic = cls.env["account.analytic.account"].create(
            {
                "name": "Tour analytic",
                "plan_id": cls.env["account.analytic.plan"]
                .create({"name": "Tour plan"})
                .id,
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
                            "analytic_distribution": {str(analytic.id): 100},
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

    def _start_tour(self, name):
        self.start_tour(
            f"/odoo/action-account_financial_report.{ACTIONS[name]}",
            f"account_financial_report_{name}",
            login=self.env.user.login,
        )

    def test_trial_balance_html_tour(self):
        self._start_tour("trial_balance_html")

    def test_trial_balance_analytic_html_tour(self):
        self._start_tour("trial_balance_analytic_html")

    def test_general_ledger_html_tour(self):
        self._start_tour("general_ledger_html")

    def test_journal_ledger_html_tour(self):
        self._start_tour("journal_ledger_html")

    def test_open_items_html_tour(self):
        self._start_tour("open_items_html")

    def test_aged_partner_balance_html_tour(self):
        self._start_tour("aged_partner_balance_html")

    def test_vat_report_html_tour(self):
        self._start_tour("vat_report_html")

    def test_vat_report_taxgroups_html_tour(self):
        self._start_tour("vat_report_taxgroups_html")

    def test_age_report_configuration_tour(self):
        self._start_tour("age_report_configuration")
