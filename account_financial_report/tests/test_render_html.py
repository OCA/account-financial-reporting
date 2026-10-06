# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree

from odoo import Command, fields
from odoo.tests import tagged
from odoo.tools.safe_eval import datetime, safe_eval, time

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

REPORTS = {
    "general": (
        "general.ledger.report.wizard",
        "action_print_report_general_ledger_html",
        "action_report_general_ledger_xlsx",
    ),
    "trial": (
        "trial.balance.report.wizard",
        "action_report_trial_balance_html",
        "action_report_trial_balance_xlsx",
    ),
    "journal": (
        "journal.ledger.report.wizard",
        "action_print_journal_ledger_wizard_html",
        "action_report_journal_ledger_xlsx",
    ),
    "open_items": (
        "open.items.report.wizard",
        "action_print_report_open_items_html",
        "action_report_open_items_xlsx",
    ),
    "aged": (
        "aged.partner.balance.report.wizard",
        "action_print_report_aged_partner_balance_html",
        "action_report_aged_partner_balance_xlsx",
    ),
    "vat": (
        "vat.report.wizard",
        "action_print_report_vat_report_html",
        "action_report_vat_report_xlsx",
    ),
}


@tagged("post_install", "-at_install")
class TestRenderHtml(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.receivable = cls.company_data["default_account_receivable"]
        cls.parent = cls.env["account.account"].create(
            {"code": "1", "name": "Render parent", "account_type": "income_other"}
        )
        cls.receivable.parent_id = cls.parent
        cls.today = fields.Date.today()
        cls.date_from = cls.today.replace(month=1, day=1)
        cls.tax = cls.company_data["default_tax_sale"]
        cls.analytic = cls.env["account.analytic.account"].create(
            {
                "name": "Render analytic",
                "plan_id": cls.env["account.analytic.plan"]
                .create({"name": "Render plan"})
                .id,
            }
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner_a.id,
                "invoice_date": cls.today,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Render line",
                            "quantity": 1,
                            "price_unit": 200,
                            "tax_ids": [Command.set(cls.tax.ids)],
                            "analytic_distribution": {str(cls.analytic.id): 100},
                        }
                    )
                ],
            }
        )
        cls.invoice.action_post()
        cls.env.flush_all()
        cls.draft = cls.env["account.move"].create(
            {
                "move_type": "entry",
                "date": cls.today,
                "line_ids": [
                    Command.create(
                        {"debit": 10, "account_id": cls.receivable.id},
                    ),
                    Command.create(
                        {
                            "credit": 10,
                            "account_id": cls.company_data[
                                "default_account_revenue"
                            ].id,
                        }
                    ),
                ],
            }
        )

    def _wizard_values(self, key, **values):
        base = {
            "general": {"date_from": self.date_from, "date_to": self.today},
            "trial": {"date_from": self.date_from, "date_to": self.today},
            "journal": {"date_from": self.date_from, "date_to": self.today},
            "open_items": {
                "date_at": self.today,
                "account_ids": [Command.set(self.receivable.ids)],
            },
            "aged": {
                "date_at": self.today,
                "account_ids": [Command.set(self.receivable.ids)],
            },
            "vat": {"date_from": self.date_from, "date_to": self.today},
        }[key]
        return {"company_id": self.company.id, **base, **values}

    def _render(self, key, **values):
        model, html_ref, xlsx_ref = REPORTS[key]
        wizard = self.env[model].create(self._wizard_values(key, **values))
        data = wizard._prepare_report_data()
        if isinstance(data.get("date_at"), type(self.today)):
            data["date_at"] = data["date_at"].isoformat()
        report = self.env["ir.actions.report"].with_context(
            active_model=wizard._name,
            active_id=wizard.id,
            active_ids=wizard.ids,
        )
        content, content_type = report._render_qweb_html(
            f"account_financial_report.{html_ref}", wizard.ids, data
        )
        self.assertEqual(content_type, "html")
        xlsx, xlsx_type = report._render_xlsx(
            f"account_financial_report.{xlsx_ref}", wizard.ids, data
        )
        self.assertEqual(xlsx_type, "xlsx")
        self.assertTrue(xlsx)
        html = content.decode()
        self._check_links(html)
        return html

    def _check_links(self, html):
        """Every link of the report must open a record or a valid search."""
        root = etree.fromstring(html, etree.HTMLParser())
        for element in root.xpath("//*[@res-model]"):
            model = element.get("res-model")
            if element.get("domain"):
                domain = safe_eval(
                    element.get("domain"), {"datetime": datetime, "time": time}
                )
                self.env[model].search_count(domain)
            if element.get("res-id"):
                self.assertTrue(self.env[model].browse(int(element.get("res-id"))))

    def _check_variants(self, key, variants, expected=None):
        for values in variants:
            with self.subTest(report=key, values=values):
                html = self._render(key, **values)
                if expected:
                    self.assertIn(expected, html)

    def test_general_ledger(self):
        variants = [{}, {"centralize": False}, {"foreign_currency": True}]
        variants += [{"grouped_by": group} for group in ("none", "partners", "taxes")]
        variants += [
            {"show_cost_center": False},
            {"hide_account_at_0": False, "target_move": "all"},
        ]
        self._check_variants("general", variants)
        self.assertIn(self.partner_a.name, self._render("general"))

    def test_trial_balance(self):
        variants = [
            {},
            {"show_partner_details": True},
            {"foreign_currency": True},
            {"grouped_by": "analytic_account"},
            {"grouped_by": "analytic_account", "foreign_currency": True},
            {"hide_account_at_0": False, "target_move": "all"},
            {"show_hierarchy": True},
            {"show_hierarchy": True, "foreign_currency": True},
            {"show_hierarchy": True, "limit_hierarchy_level": True},
            {
                "show_hierarchy": True,
                "limit_hierarchy_level": True,
                "show_hierarchy_level": 2,
                "hide_parent_hierarchy_level": True,
            },
        ]
        self._check_variants("trial", variants)

    def test_trial_balance_group_by_analytic_account(self):
        html = self._render("trial", grouped_by="analytic_account")
        self.assertIn(self.analytic.name, html)

    def test_trial_balance_hierarchy_levels(self):
        html = self._render("trial", show_hierarchy=True)
        self.assertIn("Render parent", html)
        self.assertIn(self.receivable.code, html)
        html = self._render(
            "trial",
            show_hierarchy=True,
            limit_hierarchy_level=True,
            show_hierarchy_level=1,
        )
        self.assertIn("Render parent", html)
        self.assertNotIn(self.receivable.name, html)

    def test_journal_ledger(self):
        variants = [{}, {"foreign_currency": True}, {"with_account_name": True}]
        variants += [{"sort_option": sort} for sort in ("move_name", "date")]
        variants += [{"group_option": group} for group in ("journal", "none")]
        variants += [{"move_target": target} for target in ("all", "posted", "draft")]
        variants += [{"with_auto_sequence": True}]
        self._check_variants("journal", variants)
        self.assertIn(self.invoice.name, self._render("journal"))

    def test_open_items(self):
        variants = [
            {},
            {"show_partner_details": False},
            {"foreign_currency": True},
            {"grouped_by": "salesperson"},
            {"target_move": "all", "hide_account_at_0": False},
        ]
        self._check_variants("open_items", variants)
        self.assertIn(self.partner_a.name, self._render("open_items"))

    def test_aged_partner_balance(self):
        variants = [{}, {"show_move_line_details": True}, {"target_move": "all"}]
        self._check_variants("aged", variants)
        self.assertIn(self.partner_a.name, self._render("aged"))

    def test_vat_report(self):
        variants = [{}, {"tax_detail": True}, {"based_on": "taxgroups"}]
        variants += [{"based_on": "taxgroups", "tax_detail": True}]
        self._check_variants("vat", variants)
