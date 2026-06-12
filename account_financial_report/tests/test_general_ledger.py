# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from datetime import date

from odoo import api, fields
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestGeneralLedgerReport(AccountTestInvoicingCommon):
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
        cls.before_previous_fy_year = fields.Date.from_string("2014-05-05")
        cls.previous_fy_date_start = fields.Date.from_string("2015-01-01")
        cls.previous_fy_date_end = fields.Date.from_string("2015-12-31")
        cls.fy_date_start = fields.Date.from_string("2016-01-01")
        cls.fy_date_end = fields.Date.from_string("2016-12-31")
        # Get accounts
        cls.receivable_account = cls.company_data["default_account_receivable"]
        cls.income_account = cls.company_data["default_account_revenue"]
        cls.unaffected_account = cls.env["account.account"].search(
            [
                (
                    "account_type",
                    "=",
                    "equity_unaffected",
                ),
                ("company_ids", "in", [cls.env.user.company_id.id]),
            ],
            limit=1,
        )
        cls.partner = cls.partner_a

    def _add_move(
        self,
        date,
        receivable_debit,
        receivable_credit,
        income_debit,
        income_credit,
        unaffected_debit=0,
        unaffected_credit=0,
    ):
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.env.user.company_id.id)], limit=1
        )
        partner = self.partner_a
        move_vals = {
            "journal_id": journal.id,
            "date": date,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "debit": receivable_debit,
                        "credit": receivable_credit,
                        "account_id": self.receivable_account.id,
                        "partner_id": partner.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "debit": income_debit,
                        "credit": income_credit,
                        "account_id": self.income_account.id,
                        "partner_id": partner.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "debit": unaffected_debit,
                        "credit": unaffected_credit,
                        "account_id": self.unaffected_account.id,
                        "partner_id": partner.id,
                    },
                ),
            ],
        }
        move = self.env["account.move"].create(move_vals)
        move.action_post()

    def _get_report_lines(self, with_partners=False, account_ids=False):
        centralize = True
        if with_partners:
            centralize = False
        company = self.env.user.company_id
        general_ledger = self.env["general.ledger.report.wizard"].create(
            {
                "date_from": self.fy_date_start,
                "date_to": self.fy_date_end,
                "target_move": "posted",
                "hide_account_at_0": False,
                "company_id": company.id,
                "account_ids": account_ids,
                "fy_start_date": self.fy_date_start,
                "centralize": centralize,
            }
        )
        data = general_ledger._prepare_report_data()
        res_data = self.env[
            "report.account_financial_report.general_ledger"
        ]._get_report_values(general_ledger, data)
        return res_data

    @api.model
    def check_account_in_report(self, account_id, general_ledger):
        account_in_report = False
        for account in general_ledger:
            if account["id"] == account_id:
                account_in_report = True
                break
        return account_in_report

    @api.model
    def check_partner_in_report(self, account_id, partner_id, general_ledger):
        partner_in_report = False
        for account in general_ledger:
            if account["id"] == account_id and account["partners"]:
                for partner in account["list_grouped"]:
                    if partner["id"] == partner_id:
                        partner_in_report = True
        return partner_in_report

    @api.model
    def _get_initial_balance(self, account_id, general_ledger):
        initial_balance = False
        for account in general_ledger:
            if account["id"] == account_id:
                initial_balance = account["init_bal"]
        return initial_balance

    @api.model
    def _get_partner_initial_balance(self, account_id, partner_id, general_ledger):
        initial_balance = False
        for account in general_ledger:
            if account["id"] == account_id and account["partners"]:
                for partner in account["list_grouped"]:
                    if partner["id"] == partner_id:
                        initial_balance = partner["init_bal"]
        return initial_balance

    @api.model
    def _get_final_balance(self, account_id, general_ledger):
        final_balance = False
        for account in general_ledger:
            if account["id"] == account_id:
                final_balance = account["fin_bal"]
        return final_balance

    @api.model
    def _get_partner_final_balance(self, account_id, partner_id, general_ledger):
        final_balance = False
        for account in general_ledger:
            if account["id"] == account_id and account["partners"]:
                for partner in account["list_grouped"]:
                    if partner["id"] == partner_id:
                        final_balance = partner["fin_bal"]
        return final_balance

    def test_01_account_balance(self):
        # Generate the general ledger line
        res_data = self._get_report_lines()
        general_ledger = res_data["general_ledger"]
        check_receivable_account = self.check_account_in_report(
            self.receivable_account.id, general_ledger
        )
        self.assertFalse(check_receivable_account)
        check_income_account = self.check_account_in_report(
            self.income_account.id, general_ledger
        )
        self.assertFalse(check_income_account)
        self.assertTrue(
            self.check_account_in_report(self.unaffected_account.id, general_ledger)
        )

        # Add a move at the previous day of the first day of fiscal year
        # to check the initial balance
        self._add_move(
            date=self.previous_fy_date_end,
            receivable_debit=1000,
            receivable_credit=0,
            income_debit=0,
            income_credit=1000,
        )

        # Re Generate the general ledger line
        res_data = self._get_report_lines()
        general_ledger = res_data["general_ledger"]
        check_receivable_account = self.check_account_in_report(
            self.receivable_account.id, general_ledger
        )
        self.assertTrue(check_receivable_account)
        check_income_account = self.check_account_in_report(
            self.income_account.id, general_ledger
        )
        self.assertFalse(check_income_account)

        # Check the initial and final balance
        receivable_init_balance = self._get_initial_balance(
            self.receivable_account.id, general_ledger
        )
        receivable_fin_balance = self._get_final_balance(
            self.receivable_account.id, general_ledger
        )

        self.assertEqual(receivable_init_balance["debit"], 1000)
        self.assertEqual(receivable_init_balance["credit"], 0)
        self.assertEqual(receivable_init_balance["balance"], 1000)
        self.assertEqual(receivable_fin_balance["debit"], 1000)
        self.assertEqual(receivable_fin_balance["credit"], 0)
        self.assertEqual(receivable_fin_balance["balance"], 1000)

        # Add reversale move of the initial move the first day of fiscal year
        # to check the first day of fiscal year is not used
        # to compute the initial balance
        self._add_move(
            date=self.fy_date_start,
            receivable_debit=0,
            receivable_credit=1000,
            income_debit=1000,
            income_credit=0,
        )

        # Re Generate the general ledger line
        res_data = self._get_report_lines()
        general_ledger = res_data["general_ledger"]
        check_receivable_account = self.check_account_in_report(
            self.receivable_account.id, general_ledger
        )
        self.assertTrue(check_receivable_account)
        check_income_account = self.check_account_in_report(
            self.income_account.id, general_ledger
        )
        self.assertTrue(check_income_account)

        # Check the initial and final balance
        receivable_init_balance = self._get_initial_balance(
            self.receivable_account.id, general_ledger
        )
        receivable_fin_balance = self._get_final_balance(
            self.receivable_account.id, general_ledger
        )
        income_init_balance = self._get_initial_balance(
            self.income_account.id, general_ledger
        )
        income_fin_balance = self._get_final_balance(
            self.income_account.id, general_ledger
        )

        self.assertEqual(receivable_init_balance["debit"], 1000)
        self.assertEqual(receivable_init_balance["credit"], 0)
        self.assertEqual(receivable_init_balance["balance"], 1000)
        self.assertEqual(receivable_fin_balance["debit"], 1000)
        self.assertEqual(receivable_fin_balance["credit"], 1000)
        self.assertEqual(receivable_fin_balance["balance"], 0)

        self.assertEqual(income_init_balance["debit"], 0)
        self.assertEqual(income_init_balance["credit"], 0)
        self.assertEqual(income_init_balance["balance"], 0)
        self.assertEqual(income_fin_balance["debit"], 1000)
        self.assertEqual(income_fin_balance["credit"], 0)
        self.assertEqual(income_fin_balance["balance"], 1000)

        # Re Generate the general ledger line
        res_data = self._get_report_lines(
            account_ids=(self.receivable_account + self.income_account).ids
        )
        general_ledger = res_data["general_ledger"]
        self.assertTrue(
            self.check_account_in_report(self.receivable_account.id, general_ledger)
        )
        self.assertTrue(
            self.check_account_in_report(self.income_account.id, general_ledger)
        )
        self.assertFalse(
            self.check_account_in_report(self.unaffected_account.id, general_ledger)
        )

        # Add another move at the end day of fiscal year
        # to check that it correctly used on report
        self._add_move(
            date=self.fy_date_end,
            receivable_debit=0,
            receivable_credit=1000,
            income_debit=1000,
            income_credit=0,
        )

        # Re Generate the general ledger line
        res_data = self._get_report_lines()
        general_ledger = res_data["general_ledger"]
        check_receivable_account = self.check_account_in_report(
            self.receivable_account.id, general_ledger
        )
        self.assertTrue(check_receivable_account)
        check_income_account = self.check_account_in_report(
            self.income_account.id, general_ledger
        )
        self.assertTrue(check_income_account)

        # Check the initial and final balance
        receivable_init_balance = self._get_initial_balance(
            self.receivable_account.id, general_ledger
        )
        receivable_fin_balance = self._get_final_balance(
            self.receivable_account.id, general_ledger
        )
        income_init_balance = self._get_initial_balance(
            self.income_account.id, general_ledger
        )
        income_fin_balance = self._get_final_balance(
            self.income_account.id, general_ledger
        )

        self.assertEqual(receivable_init_balance["debit"], 1000)
        self.assertEqual(receivable_init_balance["credit"], 0)
        self.assertEqual(receivable_init_balance["balance"], 1000)
        self.assertEqual(receivable_fin_balance["debit"], 1000)
        self.assertEqual(receivable_fin_balance["credit"], 2000)
        self.assertEqual(receivable_fin_balance["balance"], -1000)

        self.assertEqual(income_init_balance["debit"], 0)
        self.assertEqual(income_init_balance["credit"], 0)
        self.assertEqual(income_init_balance["balance"], 0)
        self.assertEqual(income_fin_balance["debit"], 2000)
        self.assertEqual(income_fin_balance["credit"], 0)
        self.assertEqual(income_fin_balance["balance"], 2000)

    def test_02_partner_balance(self):
        # Generate the general ledger line
        res_data = self._get_report_lines(with_partners=True)
        general_ledger = res_data["general_ledger"]
        check_partner = self.check_partner_in_report(
            self.receivable_account.id, self.partner.id, general_ledger
        )
        self.assertFalse(check_partner)

        # Add a move at the previous day of the first day of fiscal year
        # to check the initial balance
        self._add_move(
            date=self.previous_fy_date_end,
            receivable_debit=1000,
            receivable_credit=0,
            income_debit=0,
            income_credit=1000,
        )

        # Re Generate the general ledger line
        res_data = self._get_report_lines(with_partners=True)
        general_ledger = res_data["general_ledger"]
        check_partner = self.check_partner_in_report(
            self.receivable_account.id, self.partner.id, general_ledger
        )
        self.assertTrue(check_partner)

        # Check the initial and final balance
        partner_initial_balance = self._get_partner_initial_balance(
            self.receivable_account.id, self.partner.id, general_ledger
        )
        partner_final_balance = self._get_partner_final_balance(
            self.receivable_account.id, self.partner.id, general_ledger
        )

        self.assertEqual(partner_initial_balance["debit"], 1000)
        self.assertEqual(partner_initial_balance["credit"], 0)
        self.assertEqual(partner_initial_balance["balance"], 1000)
        self.assertEqual(partner_final_balance["debit"], 1000)
        self.assertEqual(partner_final_balance["credit"], 0)
        self.assertEqual(partner_final_balance["balance"], 1000)

        # Add reversale move of the initial move the first day of fiscal year
        # to check the first day of fiscal year is not used
        # to compute the initial balance
        self._add_move(
            date=self.fy_date_start,
            receivable_debit=0,
            receivable_credit=1000,
            income_debit=1000,
            income_credit=0,
        )

        # Re Generate the general ledger line
        res_data = self._get_report_lines(with_partners=True)
        general_ledger = res_data["general_ledger"]
        check_partner = self.check_partner_in_report(
            self.receivable_account.id, self.partner.id, general_ledger
        )
        self.assertTrue(check_partner)

        # Check the initial and final balance
        partner_initial_balance = self._get_partner_initial_balance(
            self.receivable_account.id, self.partner.id, general_ledger
        )
        partner_final_balance = self._get_partner_final_balance(
            self.receivable_account.id, self.partner.id, general_ledger
        )

        self.assertEqual(partner_initial_balance["debit"], 1000)
        self.assertEqual(partner_initial_balance["credit"], 0)
        self.assertEqual(partner_initial_balance["balance"], 1000)
        self.assertEqual(partner_final_balance["debit"], 1000)
        self.assertEqual(partner_final_balance["credit"], 1000)
        self.assertEqual(partner_final_balance["balance"], 0)

        # Add another move at the end day of fiscal year
        # to check that it correctly used on report
        self._add_move(
            date=self.fy_date_end,
            receivable_debit=0,
            receivable_credit=1000,
            income_debit=1000,
            income_credit=0,
        )

        # Re Generate the general ledger line
        res_data = self._get_report_lines(with_partners=True)
        general_ledger = res_data["general_ledger"]
        check_partner = self.check_partner_in_report(
            self.receivable_account.id, self.partner.id, general_ledger
        )
        self.assertTrue(check_partner)

        # Check the initial and final balance
        partner_initial_balance = self._get_partner_initial_balance(
            self.receivable_account.id, self.partner.id, general_ledger
        )
        partner_final_balance = self._get_partner_final_balance(
            self.receivable_account.id, self.partner.id, general_ledger
        )

        self.assertEqual(partner_initial_balance["debit"], 1000)
        self.assertEqual(partner_initial_balance["credit"], 0)
        self.assertEqual(partner_initial_balance["balance"], 1000)
        self.assertEqual(partner_final_balance["debit"], 1000)
        self.assertEqual(partner_final_balance["credit"], 2000)
        self.assertEqual(partner_final_balance["balance"], -1000)

    def test_03_unaffected_account_balance(self):
        # Generate the general ledger line
        res_data = self._get_report_lines()
        general_ledger = res_data["general_ledger"]
        check_unaffected_account = self.check_account_in_report(
            self.unaffected_account.id, general_ledger
        )
        self.assertTrue(check_unaffected_account)

        # Check the initial and final balance
        unaffected_init_balance = self._get_initial_balance(
            self.unaffected_account.id, general_ledger
        )
        unaffected_fin_balance = self._get_final_balance(
            self.unaffected_account.id, general_ledger
        )

        self.assertEqual(unaffected_init_balance["debit"], 0)
        self.assertEqual(unaffected_init_balance["credit"], 0)
        self.assertEqual(unaffected_init_balance["balance"], 0)
        self.assertEqual(unaffected_fin_balance["debit"], 0)
        self.assertEqual(unaffected_fin_balance["credit"], 0)
        self.assertEqual(unaffected_fin_balance["balance"], 0)

        # Add a move at the previous day of the first day of fiscal year
        # to check the initial balance
        self._add_move(
            date=self.previous_fy_date_end,
            receivable_debit=1000,
            receivable_credit=0,
            income_debit=0,
            income_credit=1000,
        )

        # Re Generate the general ledger line
        res_data = self._get_report_lines()
        general_ledger = res_data["general_ledger"]
        check_unaffected_account = self.check_account_in_report(
            self.unaffected_account.id, general_ledger
        )
        self.assertTrue(check_unaffected_account)

        # Check the initial and final balance
        unaffected_init_balance = self._get_initial_balance(
            self.unaffected_account.id, general_ledger
        )
        unaffected_fin_balance = self._get_final_balance(
            self.unaffected_account.id, general_ledger
        )

        self.assertEqual(unaffected_init_balance["debit"], 0)
        self.assertEqual(unaffected_init_balance["credit"], 1000)
        self.assertEqual(unaffected_init_balance["balance"], -1000)
        self.assertEqual(unaffected_fin_balance["debit"], 0)
        self.assertEqual(unaffected_fin_balance["credit"], 1000)
        self.assertEqual(unaffected_fin_balance["balance"], -1000)

        # Add reversale move of the initial move the first day of fiscal year
        # to check the first day of fiscal year is not used
        # to compute the initial balance
        self._add_move(
            date=self.fy_date_start,
            receivable_debit=0,
            receivable_credit=0,
            income_debit=0,
            income_credit=1000,
            unaffected_debit=1000,
            unaffected_credit=0,
        )

        # Re Generate the general ledger line
        res_data = self._get_report_lines()
        general_ledger = res_data["general_ledger"]
        check_unaffected_account = self.check_account_in_report(
            self.unaffected_account.id, general_ledger
        )
        self.assertTrue(check_unaffected_account)

        # Check the initial and final balance
        unaffected_init_balance = self._get_initial_balance(
            self.unaffected_account.id, general_ledger
        )
        unaffected_fin_balance = self._get_final_balance(
            self.unaffected_account.id, general_ledger
        )

        self.assertEqual(unaffected_init_balance["debit"], 0)
        self.assertEqual(unaffected_init_balance["credit"], 1000)
        self.assertEqual(unaffected_init_balance["balance"], -1000)
        self.assertEqual(unaffected_fin_balance["debit"], 1000)
        self.assertEqual(unaffected_fin_balance["credit"], 1000)
        self.assertEqual(unaffected_fin_balance["balance"], 0)

        # Add another move at the end day of fiscal year
        # to check that it correctly used on report
        self._add_move(
            date=self.fy_date_end,
            receivable_debit=3000,
            receivable_credit=0,
            income_debit=0,
            income_credit=0,
            unaffected_debit=0,
            unaffected_credit=3000,
        )

        # Re Generate the general ledger line
        res_data = self._get_report_lines()
        general_ledger = res_data["general_ledger"]
        check_unaffected_account = self.check_account_in_report(
            self.unaffected_account.id, general_ledger
        )
        self.assertTrue(check_unaffected_account)

        # Check the initial and final balance
        unaffected_init_balance = self._get_initial_balance(
            self.unaffected_account.id, general_ledger
        )
        unaffected_fin_balance = self._get_final_balance(
            self.unaffected_account.id, general_ledger
        )

        self.assertEqual(unaffected_init_balance["debit"], 0)
        self.assertEqual(unaffected_init_balance["credit"], 1000)
        self.assertEqual(unaffected_init_balance["balance"], -1000)
        self.assertEqual(unaffected_fin_balance["debit"], 1000)
        self.assertEqual(unaffected_fin_balance["credit"], 4000)
        self.assertEqual(unaffected_fin_balance["balance"], -3000)

    def test_04_unaffected_account_balance_2_years(self):
        # Generate the general ledger line
        res_data = self._get_report_lines()
        general_ledger = res_data["general_ledger"]
        check_unaffected_account = self.check_account_in_report(
            self.unaffected_account.id, general_ledger
        )
        self.assertTrue(check_unaffected_account)

        # Check the initial and final balance
        unaffected_init_balance = self._get_initial_balance(
            self.unaffected_account.id, general_ledger
        )
        unaffected_fin_balance = self._get_final_balance(
            self.unaffected_account.id, general_ledger
        )

        self.assertEqual(unaffected_init_balance["debit"], 0)
        self.assertEqual(unaffected_init_balance["credit"], 0)
        self.assertEqual(unaffected_init_balance["balance"], 0)
        self.assertEqual(unaffected_fin_balance["debit"], 0)
        self.assertEqual(unaffected_fin_balance["credit"], 0)
        self.assertEqual(unaffected_fin_balance["balance"], 0)

        # Add a move at any date 2 years before the balance
        # (to create an historic)
        self._add_move(
            date=self.before_previous_fy_year,
            receivable_debit=0,
            receivable_credit=1000,
            income_debit=1000,
            income_credit=0,
        )

        # Re Generate the general ledger line
        res_data = self._get_report_lines()
        general_ledger = res_data["general_ledger"]
        check_unaffected_account = self.check_account_in_report(
            self.unaffected_account.id, general_ledger
        )
        self.assertTrue(check_unaffected_account)

        # Check the initial and final balance
        unaffected_init_balance = self._get_initial_balance(
            self.unaffected_account.id, general_ledger
        )
        unaffected_fin_balance = self._get_final_balance(
            self.unaffected_account.id, general_ledger
        )

        self.assertEqual(unaffected_init_balance["debit"], 1000)
        self.assertEqual(unaffected_init_balance["credit"], 0)
        self.assertEqual(unaffected_init_balance["balance"], 1000)
        self.assertEqual(unaffected_fin_balance["debit"], 1000)
        self.assertEqual(unaffected_fin_balance["credit"], 0)
        self.assertEqual(unaffected_fin_balance["balance"], 1000)

        # Affect the company's result last year
        self._add_move(
            date=self.previous_fy_date_start,
            receivable_debit=1000,
            receivable_credit=0,
            income_debit=0,
            income_credit=0,
            unaffected_debit=0,
            unaffected_credit=1000,
        )

        # Add another move last year to test the initial balance this year
        self._add_move(
            date=self.previous_fy_date_start,
            receivable_debit=0,
            receivable_credit=500,
            income_debit=500,
            income_credit=0,
            unaffected_debit=0,
            unaffected_credit=0,
        )

        # Re Generate the general ledger line
        res_data = self._get_report_lines()
        general_ledger = res_data["general_ledger"]
        check_unaffected_account = self.check_account_in_report(
            self.unaffected_account.id, general_ledger
        )
        self.assertTrue(check_unaffected_account)

        # Check the initial and final balance
        unaffected_init_balance = self._get_initial_balance(
            self.unaffected_account.id, general_ledger
        )
        unaffected_fin_balance = self._get_final_balance(
            self.unaffected_account.id, general_ledger
        )

        self.assertEqual(unaffected_init_balance["debit"], 1500)
        self.assertEqual(unaffected_init_balance["credit"], 1000)
        self.assertEqual(unaffected_init_balance["balance"], 500)
        self.assertEqual(unaffected_fin_balance["debit"], 1500)
        self.assertEqual(unaffected_fin_balance["credit"], 1000)
        self.assertEqual(unaffected_fin_balance["balance"], 500)

    def test_partner_filter(self):
        partner_1 = self.partner_a
        partner_2 = self.partner_a.copy()
        partner_3 = self.partner_b
        partner_4 = self.partner_b.copy({"name": "Other partner"})
        partner_1.write({"is_company": False, "parent_id": partner_2.id})
        partner_3.write({"is_company": False})

        expected_list = [partner_2.id, partner_3.id, partner_4.id]
        context = {
            "active_ids": [partner_1.id, partner_2.id, partner_3.id, partner_4.id],
            "active_model": "res.partner",
        }

        wizard = self.env["general.ledger.report.wizard"].with_context(**context)
        self.assertEqual(wizard._default_partners(), expected_list)

    def test_analytic_distribution_xlsx(self):
        """
        Render the XLSX report when a journal item is distributed among
        several analytic accounts.

        In that case ``analytic_distribution`` keys are several analytic
        account ids joined by commas (e.g. ``"337,357"``), so the report must
        not try to cast the whole key with ``int()``.
        """
        company = self.env.user.company_id
        # Two analytic accounts in different plans so they can be combined in a
        # single distribution key.
        plan_1 = self.env["account.analytic.plan"].create({"name": "Plan 1"})
        plan_2 = self.env["account.analytic.plan"].create({"name": "Plan 2"})
        analytic_account_1 = self.env["account.analytic.account"].create(
            {"name": "Analytic 1", "plan_id": plan_1.id}
        )
        analytic_account_2 = self.env["account.analytic.account"].create(
            {"name": "Analytic 2", "plan_id": plan_2.id}
        )
        journal = self.env["account.journal"].search(
            [("company_id", "=", company.id)], limit=1
        )
        move = self.env["account.move"].create(
            {
                "journal_id": journal.id,
                "date": self.fy_date_start,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "debit": 1000,
                            "credit": 0,
                            "account_id": self.receivable_account.id,
                            "partner_id": self.partner.id,
                            # The receivable account is grouped by partner, so
                            # this line exercises the buggy report branch.
                            "analytic_distribution": {
                                f"{analytic_account_1.id},{analytic_account_2.id}": 100,
                            },
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 0,
                            "credit": 1000,
                            "account_id": self.income_account.id,
                            "partner_id": self.partner.id,
                        },
                    ),
                ],
            }
        )
        move.action_post()
        wizard = self.env["general.ledger.report.wizard"].create(
            {
                "date_from": self.fy_date_start,
                "date_to": self.fy_date_end,
                "target_move": "posted",
                "hide_account_at_0": False,
                "company_id": company.id,
                "fy_start_date": self.fy_date_start,
                # Lines must not be centralized so the analytic distribution is
                # rendered per move line.
                "centralize": False,
                "show_cost_center": True,
            }
        )
        data = wizard._prepare_report_data()
        # Mimic the context the wizard's report action provides at render time,
        # so the report can resolve the company currency from the active wizard.
        content, content_type = (
            self.env["ir.actions.report"]
            .with_context(
                active_model=wizard._name,
                active_id=wizard.id,
                active_ids=wizard.ids,
            )
            ._render_xlsx(
                "account_financial_report.action_report_general_ledger_xlsx",
                wizard.ids,
                data,
            )
        )
        self.assertTrue(content)
        self.assertEqual(content_type, "xlsx")

    def test_validate_date(self):
        company_id = self.env.user.company_id
        company_id.write({"fiscalyear_last_day": 31, "fiscalyear_last_month": "12"})
        user = self.env.ref("base.user_root").with_context(company_id=company_id.id)
        wizard = self.env["general.ledger.report.wizard"].with_context(user=user.id)
        self.assertEqual(wizard._init_date_from(), time.strftime("%Y") + "-01-01")

    def test_validate_date_range(self):
        data_type = self.env["date.range.type"].create(
            {"name": "Fiscal year", "company_id": False, "allow_overlap": False}
        )

        dr = self.env["date.range"].create(
            {
                "name": "FS2015",
                "date_start": "2018-01-01",
                "date_end": "2018-12-31",
                "type_id": data_type.id,
            }
        )

        wizard = self.env["general.ledger.report.wizard"].create(
            {"date_range_id": dr.id}
        )
        wizard.onchange_date_range_id()
        self.assertEqual(wizard.date_from, date(2018, 1, 1))
        self.assertEqual(wizard.date_to, date(2018, 12, 31))

    def test_05_onchange_account_range_no_typeerror(self):
        company_id = self.env.user.company_id.id
        acc_from = self.env["account.account"].create(
            {
                "code": "TEST43000",
                "name": "Test From",
                "account_type": "asset_receivable",
                "company_ids": [(6, 0, [company_id])],
            }
        )
        acc_to = self.env["account.account"].create(
            {
                "code": "TEST43005",
                "name": "Test To",
                "account_type": "asset_receivable",
                "company_ids": [(6, 0, [company_id])],
            }
        )
        acc_out = self.env["account.account"].create(
            {
                "code": "TEST44000",
                "name": "Test Out",
                "account_type": "asset_receivable",
                "company_ids": [(6, 0, [company_id])],
            }
        )
        wizard = (
            self.env["general.ledger.report.wizard"]
            .with_context(company_id=company_id)
            .create(
                {
                    "company_id": company_id,
                    "account_code_from": acc_from.id,
                    "account_code_to": acc_to.id,
                }
            )
        )
        wizard.on_change_account_range()
        self.assertIn(
            acc_from,
            wizard.account_ids,
            "The starting account should be in the filter.",
        )
        self.assertIn(
            acc_to, wizard.account_ids, "The ending account should be in the filter."
        )
        self.assertNotIn(
            acc_out,
            wizard.account_ids,
            "Accounts out of the range should NOT be in the filter.",
        )

    def test_06_line_subsection_excluded(self):
        """A posted move with a `line_subsection` row must not break the
        General Ledger. See the Trial Balance counterpart for the root cause.
        """
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.env.user.company_id.id)], limit=1
        )
        move = self.env["account.move"].create(
            {
                "journal_id": journal.id,
                "date": self.fy_date_start,
                "line_ids": [
                    Command.create(
                        {
                            "debit": 50.0,
                            "credit": 0.0,
                            "account_id": self.receivable_account.id,
                            "partner_id": self.partner.id,
                        }
                    ),
                    Command.create(
                        {
                            "debit": 0.0,
                            "credit": 50.0,
                            "account_id": self.income_account.id,
                            "partner_id": self.partner.id,
                        }
                    ),
                    Command.create(
                        {
                            "display_type": "line_subsection",
                            "name": "Subsection label",
                        }
                    ),
                ],
            }
        )
        move.action_post()
        self.assertIn("line_subsection", move.line_ids.mapped("display_type"))
        res_data = self._get_report_lines()
        self.assertIn("general_ledger", res_data)
        for entry in res_data["general_ledger"]:
            self.assertTrue(
                entry.get("id"),
                f"Report contains a line with falsy id: {entry}",
            )
