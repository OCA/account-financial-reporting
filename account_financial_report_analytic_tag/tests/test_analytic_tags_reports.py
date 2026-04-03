# Copyright 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.fields import Date
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAnalyticTagsReports(AccountTestInvoicingCommon):
    """Verify that the Analytic Tags column appears in each financial report."""

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
        cls.company = cls.company_data["company"]
        cls.company.account_sale_tax_id = False

        today = Date.today()
        cls.fy_date_start = today.replace(month=1, day=1)
        cls.fy_date_end = today.replace(month=12, day=31)

        cls.receivable_account = cls.company_data["default_account_receivable"]
        cls.income_account = cls.company_data["default_account_revenue"]
        cls.payable_account = cls.company_data["default_account_payable"]
        cls.expense_account = cls.company_data["default_account_expense"]
        cls.journal_sale = cls.company_data["default_journal_sale"]
        cls.journal_purchase = cls.company_data["default_journal_purchase"]
        cls.partner = cls.env.ref("base.res_partner_2")

        # Create an analytic tag to use across all test methods.
        cls.tag = cls.env["account.analytic.tag"].create({"name": "TestTag"})

    def _create_move_with_tag(self, journal, debit_account, credit_account, amount=100):
        """Post a simple journal entry where the debit line carries a tag."""
        move = self.env["account.move"].create(
            {
                "journal_id": journal.id,
                "date": Date.today(),
                "line_ids": [
                    Command.create(
                        {
                            "name": "tagged line",
                            "debit": amount,
                            "credit": 0,
                            "account_id": debit_account.id,
                            "analytic_tag_ids": [Command.link(self.tag.id)],
                        }
                    ),
                    Command.create(
                        {
                            "name": "counter line",
                            "debit": 0,
                            "credit": amount,
                            "account_id": credit_account.id,
                        }
                    ),
                ],
            }
        )
        move.action_post()
        return move

    # ------------------------------------------------------------------
    # Journal Ledger
    # ------------------------------------------------------------------

    def test_journal_ledger_show_analytic_tags(self):
        """Tags column data appears when show_analytic_tags is enabled."""
        self._create_move_with_tag(
            self.journal_sale, self.receivable_account, self.income_account
        )
        wiz = self.env["journal.ledger.report.wizard"].create(
            {
                "date_from": self.fy_date_start,
                "date_to": self.fy_date_end,
                "company_id": self.company.id,
                "journal_ids": [Command.set(self.journal_sale.ids)],
                "move_target": "posted",
                "show_analytic_tags": True,
            }
        )
        data = wiz._prepare_report_data()
        self.assertTrue(data["show_analytic_tags"])

        report = self.env["report.account_financial_report.journal_ledger"]
        res = report._get_report_values(wiz, data)

        self.assertTrue(res.get("show_analytic_tags"))

        # Label column must be narrower when both flags are active.
        label_style_on = res["label_column_style"]

        wiz.show_analytic_tags = False
        data_off = wiz._prepare_report_data()
        res_off = report._get_report_values(wiz, data_off)
        self.assertNotEqual(res_off["label_column_style"], label_style_on)

        # The tagged line should carry a non-empty display string.
        tagged_line = None
        for move_data in res["Moves"]:
            for ml in move_data["report_move_lines"]:
                if ml.get("tag_ids"):
                    tagged_line = ml
                    break
        self.assertIsNotNone(tagged_line, "Expected a move line with tag_ids")
        self.assertIn(self.tag.id, tagged_line["tag_ids"])
        self.assertIn(self.tag.name, tagged_line["tag_display"])

    # ------------------------------------------------------------------
    # General Ledger
    # ------------------------------------------------------------------

    def test_general_ledger_show_analytic_tags(self):
        """Tags column data appears in the general ledger when enabled."""
        self._create_move_with_tag(
            self.journal_sale, self.receivable_account, self.income_account
        )
        wiz = self.env["general.ledger.report.wizard"].create(
            {
                "date_from": self.fy_date_start,
                "date_to": self.fy_date_end,
                "company_id": self.company.id,
                "show_analytic_tags": True,
            }
        )
        data = wiz._prepare_report_data()
        self.assertTrue(data["show_analytic_tags"])

        report = self.env["report.account_financial_report.general_ledger"]
        res = report._get_report_values(wiz, data)

        self.assertTrue(res.get("show_analytic_tags"))
        self.assertIn("tags_data", res)
        self.assertIn(self.tag.id, res["tags_data"])

        # Every move line dict must have the renamed 'tag_ids' key.
        tagged_line = None
        for account in res["general_ledger"]:
            for ml in report._iter_gl_move_lines(account):
                if ml.get("tag_ids"):
                    tagged_line = ml
                    break
        self.assertIsNotNone(tagged_line, "Expected a move line with tag_ids")
        self.assertIn(self.tag.id, tagged_line["tag_ids"])
        self.assertIn(self.tag.name, tagged_line["tag_display"])

        # Ref-label column must be narrower with the tags column active.
        ref_label_on = res["ref_label_style"]
        wiz.show_analytic_tags = False
        data_off = wiz._prepare_report_data()
        res_off = report._get_report_values(wiz, data_off)
        self.assertNotEqual(res_off.get("ref_label_style"), ref_label_on)

    # ------------------------------------------------------------------
    # Open Items
    # ------------------------------------------------------------------

    def test_open_items_show_analytic_tags(self):
        """Tags column data appears in open items when enabled."""
        self._create_move_with_tag(
            self.journal_sale, self.receivable_account, self.income_account
        )
        wiz = self.env["open.items.report.wizard"].create(
            {
                "date_at": Date.today(),
                "company_id": self.company.id,
                "account_ids": [Command.set(self.receivable_account.ids)],
                "show_analytic_tags": True,
                "target_move": "posted",
            }
        )
        data = wiz._prepare_report_data()
        self.assertTrue(data["show_analytic_tags"])

        report = self.env["report.account_financial_report.open_items"]
        res = report._get_report_values(wiz, data)

        self.assertTrue(res.get("show_analytic_tags"))

        # Ref-label column must be narrower with the tags column active.
        ref_label_on = res["ref_label_style"]
        wiz.show_analytic_tags = False
        data_off = wiz._prepare_report_data()
        res_off = report._get_report_values(wiz, data_off)
        self.assertNotEqual(res_off["ref_label_style"], ref_label_on)

    # ------------------------------------------------------------------
    # Aged Partner Balance
    # ------------------------------------------------------------------

    def test_aged_partner_balance_show_analytic_tags(self):
        """Tags appear in aged partner balance move line details when enabled."""
        self._create_move_with_tag(
            self.journal_sale, self.receivable_account, self.income_account
        )
        aged_config = self.env["account.age.report.configuration"].search([], limit=1)
        wiz = self.env["aged.partner.balance.report.wizard"].create(
            {
                "date_at": Date.today(),
                "company_id": self.company.id,
                "account_ids": [Command.set(self.receivable_account.ids)],
                "show_move_line_details": True,
                "show_analytic_tags": True,
                "target_move": "posted",
                "age_partner_config_id": aged_config.id if aged_config else False,
            }
        )
        data = wiz._prepare_report_data()
        self.assertTrue(data["show_analytic_tags"])

        report = self.env["report.account_financial_report.aged_partner_balance"]
        res = report._get_report_values(wiz, data)

        self.assertTrue(res.get("show_analytic_tags"))

        # Ref-label column must be narrower with the tags column active.
        ref_label_on = res["ref_label_style"]
        wiz.show_analytic_tags = False
        data_off = wiz._prepare_report_data()
        res_off = report._get_report_values(wiz, data_off)
        self.assertNotEqual(res_off["ref_label_style"], ref_label_on)

    def test_aged_partner_balance_tags_hidden_without_move_line_details(self):
        """When show_move_line_details is False, tags flag has no effect."""
        aged_config = self.env["account.age.report.configuration"].search([], limit=1)
        wiz = self.env["aged.partner.balance.report.wizard"].create(
            {
                "date_at": Date.today(),
                "company_id": self.company.id,
                "account_ids": [Command.set(self.receivable_account.ids)],
                "show_move_line_details": False,
                "show_analytic_tags": True,
                "target_move": "posted",
                "age_partner_config_id": aged_config.id if aged_config else False,
            }
        )
        data = wiz._prepare_report_data()
        report = self.env["report.account_financial_report.aged_partner_balance"]
        res = report._get_report_values(wiz, data)
        # show_analytic_tags must be absent from the result when details are hidden.
        self.assertNotIn("show_analytic_tags", res)
