# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re

from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestTrialBalanceReport(AccountTestInvoicingCommon):
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
        group_obj = cls.env["account.account"]
        group_vals = {"account_type": "income_other"}
        cls.group1 = group_obj.create({**group_vals, "code": "1", "name": "Group 1"})
        cls.group11 = group_obj.create(
            {
                **group_vals,
                "code": "11",
                "name": "Group 11",
                "parent_id": cls.group1.id,
            }
        )
        cls.group2 = group_obj.create({**group_vals, "code": "2", "name": "Group 2"})
        # Set accounts
        cls.account001 = cls._create_account_account(
            cls,
            {
                "code": "001",
                "name": "Account 001",
                "account_type": "income_other",
            },
        )
        cls.account100 = cls.company_data["default_account_receivable"]
        cls.account110 = cls.env["account.account"].search(
            [
                (
                    "account_type",
                    "=",
                    "equity_unaffected",
                ),
            ],
            limit=1,
        )
        cls.account200 = cls._create_account_account(
            cls,
            {
                "code": "200",
                "name": "Account 200",
                "account_type": "income_other",
            },
        )
        cls.account300 = cls._create_account_account(
            cls,
            {
                "code": "300",
                "name": "Account 300",
                "account_type": "income_other",
            },
        )
        cls.account201 = cls._create_account_account(
            cls,
            {
                "code": "201",
                "name": "Account 201",
                "account_type": "income_other",
            },
        )
        cls.account100.parent_id = cls.group1
        cls.account200.parent_id = cls.group2
        cls.account201.parent_id = cls.group2
        cls.previous_fy_date_start = "2015-01-01"
        cls.previous_fy_date_end = "2015-12-31"
        cls.fy_date_start = "2016-01-01"
        cls.fy_date_end = "2016-12-31"
        cls.date_start = "2016-01-01"
        cls.date_end = "2016-12-31"
        cls.partner = cls.partner_a
        cls.unaffected_account = cls.env["account.account"].search(
            [
                (
                    "account_type",
                    "=",
                    "equity_unaffected",
                ),
            ],
            limit=1,
        )
        cls.foreign_currency = cls.setup_other_currency(
            "EUR", rates=[("1900-01-01", 2.0)]
        )

    def _create_account_account(self, vals):
        item = self.env["account.account"].create(vals)
        return item

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
                        "partner_id": partner.id,
                        "account_id": self.account100.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "debit": income_debit,
                        "credit": income_credit,
                        "partner_id": partner.id,
                        "account_id": self.account200.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "debit": unaffected_debit,
                        "credit": unaffected_credit,
                        "partner_id": partner.id,
                        "account_id": self.account110.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "debit": receivable_debit,
                        "credit": receivable_credit,
                        "partner_id": partner.id,
                        "account_id": self.account300.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "debit": receivable_credit,
                        "credit": receivable_debit,
                        "partner_id": partner.id,
                        "account_id": self.account201.id,
                    },
                ),
            ],
        }
        move = self.env["account.move"].create(move_vals)
        move.action_post()

    def _add_currency_move(self, date, debit, credit, amount_currency, currency=None):
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.env.user.company_id.id)], limit=1
        )
        move = self.env["account.move"].create(
            {
                "journal_id": journal.id,
                "date": date,
                "line_ids": [
                    Command.create(
                        {
                            "debit": debit,
                            "credit": credit,
                            "partner_id": self.partner_a.id,
                            "account_id": self.account100.id,
                            "currency_id": (currency or self.foreign_currency).id,
                            "amount_currency": amount_currency,
                        }
                    ),
                    Command.create(
                        {
                            "debit": credit,
                            "credit": debit,
                            "partner_id": self.partner_a.id,
                            "account_id": self.account200.id,
                        }
                    ),
                ],
            }
        )
        move.action_post()
        return move

    def _get_report_lines(
        self,
        with_partners=False,
        account_ids=False,
        show_hierarchy=False,
        foreign_currency=False,
    ):
        company = self.env.user.company_id
        trial_balance = self.env["trial.balance.report.wizard"].create(
            {
                "date_from": self.date_start,
                "date_to": self.date_end,
                "target_move": "posted",
                "hide_account_at_0": True,
                "show_hierarchy": show_hierarchy,
                "company_id": company.id,
                "account_ids": account_ids,
                "fy_start_date": self.fy_date_start,
                "show_partner_details": with_partners,
                "foreign_currency": foreign_currency,
            }
        )
        data = trial_balance._prepare_report_data()
        res_data = self.env[
            "report.account_financial_report.trial_balance"
        ]._get_report_values(trial_balance, data)
        return res_data

    def check_account_in_report(self, account_id, trial_balance):
        account_in_report = False
        for account in trial_balance:
            if account["id"] == account_id and account["type"] == "account_type":
                account_in_report = True
                break
        return account_in_report

    def _get_account_lines(self, account_id, trial_balance):
        lines = False
        for account in trial_balance:
            if account["id"] == account_id and account["type"] == "account_type":
                lines = {
                    "initial_balance": account["initial_balance"],
                    "debit": account["debit"],
                    "credit": account["credit"],
                    "final_balance": account["ending_balance"],
                }
        return lines

    def _get_group_lines(self, group_id, trial_balance):
        lines = False
        for group in trial_balance:
            if group["id"] == group_id and group["type"] == "group_type":
                lines = {
                    "initial_balance": group["initial_balance"],
                    "debit": group["debit"],
                    "credit": group["credit"],
                    "final_balance": group["ending_balance"],
                }
        return lines

    def check_partner_in_report(self, account_id, partner_id, total_amount):
        return account_id in total_amount and partner_id in total_amount[account_id]

    def _get_partner_lines(self, account_id, partner_id, total_amount):
        acc_id = account_id
        prt_id = partner_id
        lines = {
            "initial_balance": total_amount[acc_id][prt_id]["initial_balance"],
            "debit": total_amount[acc_id][prt_id]["debit"],
            "credit": total_amount[acc_id][prt_id]["credit"],
            "final_balance": total_amount[acc_id][prt_id]["ending_balance"],
        }
        return lines

    def _sum_all_accounts(self, trial_balance, feature):
        total = 0.0
        for account in trial_balance:
            if account["type"] == "account_type":
                for key in account:
                    if key == feature:
                        total += account[key]
        return total

    def test_00_account_group(self):
        self.assertIn(self.group1, self.account100.parent_ids)
        self.assertIn(self.group2, self.account200.parent_ids)

    def test_02_account_balance_hierarchy(self):
        # Generate the general ledger line
        res_data = self._get_report_lines(show_hierarchy=True)
        trial_balance = res_data["trial_balance"]
        check_receivable_account = self.check_account_in_report(
            self.account100.id, trial_balance
        )
        self.assertFalse(check_receivable_account)
        check_income_account = self.check_account_in_report(
            self.account200.id, trial_balance
        )
        self.assertFalse(check_income_account)

        # Add a move at the previous day of the first day of fiscal year
        # to check the initial balance
        self._add_move(
            date=self.previous_fy_date_end,
            receivable_debit=1000,
            receivable_credit=0,
            income_debit=0,
            income_credit=1000,
        )

        # Re Generate the trial balance line
        res_data = self._get_report_lines(show_hierarchy=True)
        trial_balance = res_data["trial_balance"]
        check_receivable_account = self.check_account_in_report(
            self.account100.id, trial_balance
        )
        self.assertTrue(check_receivable_account)
        check_income_account = self.check_account_in_report(
            self.account200.id, trial_balance
        )
        self.assertFalse(check_income_account)

        # Check the initial and final balance
        account_receivable_lines = self._get_account_lines(
            self.account100.id, trial_balance
        )
        group1_lines = self._get_group_lines(self.group1.id, trial_balance)

        self.assertEqual(account_receivable_lines["initial_balance"], 1000)
        self.assertEqual(account_receivable_lines["debit"], 0)
        self.assertEqual(account_receivable_lines["credit"], 0)
        self.assertEqual(account_receivable_lines["final_balance"], 1000)

        self.assertEqual(group1_lines["initial_balance"], 1000)
        self.assertEqual(group1_lines["debit"], 0)
        self.assertEqual(group1_lines["credit"], 0)
        self.assertEqual(group1_lines["final_balance"], 1000)

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

        # Re Generate the trial balance line
        res_data = self._get_report_lines(show_hierarchy=True)
        trial_balance = res_data["trial_balance"]
        check_receivable_account = self.check_account_in_report(
            self.account100.id, trial_balance
        )
        self.assertTrue(check_receivable_account)
        check_income_account = self.check_account_in_report(
            self.account200.id, trial_balance
        )
        self.assertTrue(check_income_account)

        # Check the initial and final balance
        account_receivable_lines = self._get_account_lines(
            self.account100.id, trial_balance
        )
        account_income_lines = self._get_account_lines(
            self.account200.id, trial_balance
        )
        group1_lines = self._get_group_lines(self.group1.id, trial_balance)
        group2_lines = self._get_group_lines(self.group2.id, trial_balance)

        self.assertEqual(account_receivable_lines["initial_balance"], 1000)
        self.assertEqual(account_receivable_lines["debit"], 0)
        self.assertEqual(account_receivable_lines["credit"], 1000)
        self.assertEqual(account_receivable_lines["final_balance"], 0)

        self.assertEqual(account_income_lines["initial_balance"], 0)
        self.assertEqual(account_income_lines["debit"], 1000)
        self.assertEqual(account_income_lines["credit"], 0)
        self.assertEqual(account_income_lines["final_balance"], 1000)

        self.assertEqual(group1_lines["initial_balance"], 1000)
        self.assertEqual(group1_lines["debit"], 0)
        self.assertEqual(group1_lines["credit"], 1000)
        self.assertEqual(group1_lines["final_balance"], 0)

        self.assertEqual(group2_lines["initial_balance"], 0)
        self.assertEqual(group2_lines["debit"], 2000)
        self.assertEqual(group2_lines["credit"], 0)
        self.assertEqual(group2_lines["final_balance"], 2000)

        # Add another move at the end day of fiscal year
        # to check that it correctly used on report
        self._add_move(
            date=self.fy_date_end,
            receivable_debit=0,
            receivable_credit=1000,
            income_debit=1000,
            income_credit=0,
        )

        # Re Generate the trial balance line
        res_data = self._get_report_lines(show_hierarchy=True)
        trial_balance = res_data["trial_balance"]
        check_receivable_account = self.check_account_in_report(
            self.account100.id, trial_balance
        )
        self.assertTrue(check_receivable_account)
        check_income_account = self.check_account_in_report(
            self.account200.id, trial_balance
        )
        self.assertTrue(check_income_account)

        # Check the initial and final balance
        account_receivable_lines = self._get_account_lines(
            self.account100.id, trial_balance
        )
        account_income_lines = self._get_account_lines(
            self.account200.id, trial_balance
        )
        group1_lines = self._get_group_lines(self.group1.id, trial_balance)
        group2_lines = self._get_group_lines(self.group2.id, trial_balance)

        self.assertEqual(account_receivable_lines["initial_balance"], 1000)
        self.assertEqual(account_receivable_lines["debit"], 0)
        self.assertEqual(account_receivable_lines["credit"], 2000)
        self.assertEqual(account_receivable_lines["final_balance"], -1000)

        self.assertEqual(account_income_lines["initial_balance"], 0)
        self.assertEqual(account_income_lines["debit"], 2000)
        self.assertEqual(account_income_lines["credit"], 0)
        self.assertEqual(account_income_lines["final_balance"], 2000)

        self.assertEqual(group1_lines["initial_balance"], 1000)
        self.assertEqual(group1_lines["debit"], 0)
        self.assertEqual(group1_lines["credit"], 2000)
        self.assertEqual(group1_lines["final_balance"], -1000)

        self.assertEqual(group2_lines["initial_balance"], 0)
        self.assertEqual(group2_lines["debit"], 4000)
        self.assertEqual(group2_lines["credit"], 0)
        self.assertEqual(group2_lines["final_balance"], 4000)

    def test_03_partner_balance(self):
        # Generate the trial balance line
        res_data = self._get_report_lines(with_partners=True)
        total_amount = res_data["total_amount"]
        check_partner_receivable = self.check_partner_in_report(
            self.account100.id, self.partner.id, total_amount
        )
        self.assertFalse(check_partner_receivable)

        # Add a move at the previous day of the first day of fiscal year
        # to check the initial balance
        self._add_move(
            date=self.previous_fy_date_end,
            receivable_debit=1000,
            receivable_credit=0,
            income_debit=0,
            income_credit=1000,
        )

        # Re Generate the trial balance line
        res_data = self._get_report_lines(with_partners=True)
        total_amount = res_data["total_amount"]
        check_partner_receivable = self.check_partner_in_report(
            self.account100.id, self.partner.id, total_amount
        )
        self.assertTrue(check_partner_receivable)

        # Check the initial and final balance
        partner_lines = self._get_partner_lines(
            self.account100.id, self.partner.id, total_amount
        )

        self.assertEqual(partner_lines["initial_balance"], 1000)
        self.assertEqual(partner_lines["debit"], 0)
        self.assertEqual(partner_lines["credit"], 0)
        self.assertEqual(partner_lines["final_balance"], 1000)

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

        # Re Generate the trial balance line
        res_data = self._get_report_lines(with_partners=True)
        total_amount = res_data["total_amount"]
        check_partner_receivable = self.check_partner_in_report(
            self.account100.id, self.partner.id, total_amount
        )
        self.assertTrue(check_partner_receivable)

        # Check the initial and final balance
        partner_lines = self._get_partner_lines(
            self.account100.id, self.partner.id, total_amount
        )

        self.assertEqual(partner_lines["initial_balance"], 1000)
        self.assertEqual(partner_lines["debit"], 0)
        self.assertEqual(partner_lines["credit"], 1000)
        self.assertEqual(partner_lines["final_balance"], 0)

        # Add another move at the end day of fiscal year
        # to check that it correctly used on report
        self._add_move(
            date=self.fy_date_end,
            receivable_debit=0,
            receivable_credit=1000,
            income_debit=1000,
            income_credit=0,
        )

        # Re Generate the trial balance line
        res_data = self._get_report_lines(with_partners=True)
        total_amount = res_data["total_amount"]
        check_partner_receivable = self.check_partner_in_report(
            self.account100.id, self.partner.id, total_amount
        )
        self.assertTrue(check_partner_receivable)

        # Check the initial and final balance
        partner_lines = self._get_partner_lines(
            self.account100.id, self.partner.id, total_amount
        )

        self.assertEqual(partner_lines["initial_balance"], 1000)
        self.assertEqual(partner_lines["debit"], 0)
        self.assertEqual(partner_lines["credit"], 2000)
        self.assertEqual(partner_lines["final_balance"], -1000)

    def test_04_undistributed_pl(self):
        # Add a P&L Move in the previous FY
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.env.user.company_id.id)], limit=1
        )
        move_vals = {
            "journal_id": journal.id,
            "date": self.previous_fy_date_end,
            "line_ids": [
                (
                    0,
                    0,
                    {"debit": 0.0, "credit": 1000.0, "account_id": self.account300.id},
                ),
                (
                    0,
                    0,
                    {"debit": 1000.0, "credit": 0.0, "account_id": self.account100.id},
                ),
            ],
        }
        move = self.env["account.move"].create(move_vals)
        move.action_post()
        # Generate the trial balance line
        company = self.env.user.company_id
        trial_balance = self.env["trial.balance.report.wizard"].create(
            {
                "date_from": self.date_start,
                "date_to": self.date_end,
                "target_move": "posted",
                "hide_account_at_0": False,
                "show_hierarchy": False,
                "company_id": company.id,
                "fy_start_date": self.fy_date_start,
            }
        )
        data = trial_balance._prepare_report_data()
        res_data = self.env[
            "report.account_financial_report.trial_balance"
        ]._get_report_values(trial_balance, data)
        trial_balance = res_data["trial_balance"]

        check_unaffected_account = self.check_account_in_report(
            self.unaffected_account.id, trial_balance
        )
        self.assertTrue(check_unaffected_account)

        unaffected_lines = self._get_account_lines(
            self.unaffected_account.id, trial_balance
        )

        self.assertEqual(unaffected_lines["initial_balance"], -1000)
        self.assertEqual(unaffected_lines["debit"], 0)
        self.assertEqual(unaffected_lines["credit"], 0)
        self.assertEqual(unaffected_lines["final_balance"], -1000)
        # Add a P&L Move to the current FY
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.env.user.company_id.id)], limit=1
        )
        move_vals = {
            "journal_id": journal.id,
            "date": self.date_start,
            "line_ids": [
                (
                    0,
                    0,
                    {"debit": 0.0, "credit": 1000.0, "account_id": self.account300.id},
                ),
                (
                    0,
                    0,
                    {"debit": 1000.0, "credit": 0.0, "account_id": self.account100.id},
                ),
            ],
        }
        move = self.env["account.move"].create(move_vals)
        move.action_post()
        # Re Generate the trial balance line
        trial_balance = self.env["trial.balance.report.wizard"].create(
            {
                "date_from": self.date_start,
                "date_to": self.date_end,
                "target_move": "posted",
                "hide_account_at_0": False,
                "show_hierarchy": False,
                "company_id": company.id,
                "fy_start_date": self.fy_date_start,
            }
        )
        data = trial_balance._prepare_report_data()
        res_data = self.env[
            "report.account_financial_report.trial_balance"
        ]._get_report_values(trial_balance, data)
        trial_balance = res_data["trial_balance"]
        # The unaffected earnings account is not affected by a journal entry
        # made to the P&L in the current fiscal year.
        check_unaffected_account = self.check_account_in_report(
            self.unaffected_account.id, trial_balance
        )
        self.assertTrue(check_unaffected_account)

        unaffected_lines = self._get_account_lines(
            self.unaffected_account.id, trial_balance
        )

        self.assertEqual(unaffected_lines["initial_balance"], -1000)
        self.assertEqual(unaffected_lines["debit"], 0)
        self.assertEqual(unaffected_lines["credit"], 0)
        self.assertEqual(unaffected_lines["final_balance"], -1000)
        # Add a Move including Unaffected Earnings to the current FY
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.env.user.company_id.id)], limit=1
        )
        move_vals = {
            "journal_id": journal.id,
            "date": self.date_start,
            "line_ids": [
                (
                    0,
                    0,
                    {"debit": 0.0, "credit": 1000.0, "account_id": self.account110.id},
                ),
                (
                    0,
                    0,
                    {"debit": 1000.0, "credit": 0.0, "account_id": self.account100.id},
                ),
            ],
        }
        move = self.env["account.move"].create(move_vals)
        move.action_post()
        # Re Generate the trial balance line
        trial_balance = self.env["trial.balance.report.wizard"].create(
            {
                "date_from": self.date_start,
                "date_to": self.date_end,
                "target_move": "posted",
                "hide_account_at_0": False,
                "show_hierarchy": False,
                "company_id": company.id,
                "fy_start_date": self.fy_date_start,
            }
        )
        data = trial_balance._prepare_report_data()
        res_data = self.env[
            "report.account_financial_report.trial_balance"
        ]._get_report_values(trial_balance, data)
        trial_balance = res_data["trial_balance"]
        # The unaffected earnings account affected by a journal entry
        # made to the unaffected earnings in the current fiscal year.
        check_unaffected_account = self.check_account_in_report(
            self.unaffected_account.id, trial_balance
        )
        self.assertTrue(check_unaffected_account)

        unaffected_lines = self._get_account_lines(
            self.unaffected_account.id, trial_balance
        )

        self.assertEqual(unaffected_lines["initial_balance"], -1000)
        self.assertEqual(unaffected_lines["debit"], 0)
        self.assertEqual(unaffected_lines["credit"], 1000)
        self.assertEqual(unaffected_lines["final_balance"], -2000)

        # The totals for the Trial Balance are zero
        total_initial_balance = self._sum_all_accounts(trial_balance, "initial_balance")
        total_final_balance = self._sum_all_accounts(trial_balance, "ending_balance")
        total_debit = self._sum_all_accounts(trial_balance, "debit")
        total_credit = self._sum_all_accounts(trial_balance, "credit")

        self.assertEqual(total_initial_balance, 0)
        self.assertEqual(total_final_balance, 0)
        self.assertEqual(total_debit, total_credit)

    def test_05_all_accounts_loaded(self):
        # Tests if all accounts which code is number are loaded
        # when the account_code_ fields changed
        all_accounts = (
            self.env["account.account"]
            .search([], order="code")
            .filtered(lambda acc: re.fullmatch(r"[0-9]+(\.[0-9]+)?", acc.code))
        )
        company = self.env.user.company_id
        trial_balance = self.env["trial.balance.report.wizard"].create(
            {
                "date_from": self.date_start,
                "date_to": self.date_end,
                "target_move": "posted",
                "hide_account_at_0": False,
                "show_hierarchy": False,
                "company_id": company.id,
                "fy_start_date": self.fy_date_start,
                "account_code_from": self.account001.id,
                "account_code_to": all_accounts[-1].id,
            }
        )
        trial_balance.on_change_account_range()
        # sets are needed because some codes are duplicated and
        # thus the length of all_accounts would be higher
        all_accounts_code_set = set()
        trial_balance_code_set = set()
        [all_accounts_code_set.add(account.code) for account in all_accounts]
        [
            trial_balance_code_set.add(account.code)
            for account in trial_balance.account_ids
        ]
        self.assertEqual(len(trial_balance_code_set), len(all_accounts_code_set))
        self.assertTrue(trial_balance_code_set == all_accounts_code_set)

    def test_06_line_subsection_excluded(self):
        """A posted move that contains a `line_subsection` display row must
        not break the Trial Balance.

        Odoo 19 introduced the `line_subsection` value in
        `account.move.line.display_type`. Such rows carry no `account_id`,
        so they reach `formatted_read_group` as a `False` group and the
        downstream `_compute_account_amount` raises
        `TypeError: 'bool' object is not subscriptable`.
        """
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.env.user.company_id.id)], limit=1
        )
        move = self.env["account.move"].create(
            {
                "journal_id": journal.id,
                "date": self.date_start,
                "line_ids": [
                    Command.create(
                        {
                            "debit": 100.0,
                            "credit": 0.0,
                            "account_id": self.account200.id,
                            "partner_id": self.partner_a.id,
                        }
                    ),
                    Command.create(
                        {
                            "debit": 0.0,
                            "credit": 100.0,
                            "account_id": self.account100.id,
                            "partner_id": self.partner_a.id,
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
        self.assertIn(
            "line_subsection",
            move.line_ids.mapped("display_type"),
            "Move was not created with a line_subsection row",
        )
        res_data = self._get_report_lines()
        self.assertIn("trial_balance", res_data)
        for entry in res_data["trial_balance"]:
            self.assertTrue(
                entry.get("id"),
                f"Report contains a line with falsy id: {entry}",
            )

    def test_07_foreign_currency_initial_balance(self):
        # GIVEN an initial balance in foreign currency (before the period)
        self._add_currency_move(
            date=self.previous_fy_date_end,
            debit=1000,
            credit=0,
            amount_currency=2000,
        )
        self._add_currency_move(
            date=self.date_start,
            debit=500,
            credit=0,
            amount_currency=1000,
        )

        # WHEN
        res_data = self._get_report_lines(foreign_currency=True)
        # THEN
        self.assertTrue(res_data["foreign_currency"])
        account_lines = self._get_account_lines(
            self.account100.id, res_data["trial_balance"]
        )
        self.assertTrue(account_lines)
        total = res_data["total_amount"][self.account100.id]
        self.assertEqual(total["initial_currency_balance"], 2000)
        self.assertEqual(total["ending_currency_balance"], 3000)

    def test_08_account_multicurrency_period_totals(self):
        """Period totals must include every currency group of an account."""
        company_currency = self.env.company.currency_id
        self._add_currency_move(
            date=self.date_start,
            debit=100.0,
            credit=0.0,
            amount_currency=100.0,
            currency=company_currency,
        )
        self._add_currency_move(
            date=self.date_start,
            debit=60.0,
            credit=0.0,
            amount_currency=120.0,
        )
        result = self._get_report_lines()
        account_lines = self._get_account_lines(
            self.account100.id, result["trial_balance"]
        )
        self.assertTrue(account_lines)
        self.assertEqual(account_lines["initial_balance"], 0.0)
        self.assertEqual(account_lines["debit"], 160.0)
        self.assertEqual(account_lines["credit"], 0.0)
        self.assertEqual(account_lines["final_balance"], 160.0)
        result_foreign_currency = self._get_report_lines(foreign_currency=True)
        account_lines = self._get_account_lines(
            self.account100.id, result_foreign_currency["trial_balance"]
        )
        self.assertTrue(account_lines)
        self.assertEqual(account_lines["debit"], 160.0)
        self.assertEqual(account_lines["final_balance"], 160.0)
        total = result_foreign_currency["total_amount"][self.account100.id]
        self.assertEqual(total["ending_currency_balance"], 220.0)

    def test_09_hierarchy_levels_and_xlsx(self):
        """Parent accounts give the hierarchy rows, their levels and the XLSX."""
        self.account200.parent_id = self.group11
        self._add_move(
            date=self.date_start,
            receivable_debit=1000,
            receivable_credit=0,
            income_debit=0,
            income_credit=1000,
        )
        res_data = self._get_report_lines(show_hierarchy=True)
        rows = {(row["type"], row["id"]): row for row in res_data["trial_balance"]}
        group1 = rows["group_type", self.group1.id]
        group11 = rows["group_type", self.group11.id]
        self.assertEqual(group1["level"], 0)
        self.assertEqual(group11["level"], 1)
        self.assertEqual(group11["parent_id"], self.group1.id)
        self.assertEqual(group1["debit"], 1000)
        self.assertEqual(group11["credit"], 1000)
        self.assertEqual(
            rows["account_type", self.account200.id]["level"],
            2,
        )
        wizard = self.env["trial.balance.report.wizard"].create(
            {
                "date_from": self.date_start,
                "date_to": self.date_end,
                "target_move": "posted",
                "show_hierarchy": True,
                "company_id": self.env.user.company_id.id,
                "fy_start_date": self.fy_date_start,
            }
        )
        content, content_type = (
            self.env["ir.actions.report"]
            .with_context(
                active_model=wizard._name,
                active_id=wizard.id,
                active_ids=wizard.ids,
            )
            ._render_xlsx(
                "account_financial_report.action_report_trial_balance_xlsx",
                wizard.ids,
                wizard._prepare_report_data(),
            )
        )
        self.assertEqual(content_type, "xlsx")
        self.assertTrue(content)

    def test_10_group_by_analytic_account(self):
        plan = self.env["account.analytic.plan"].create({"name": "Plan"})
        analytic = self.env["account.analytic.account"].create(
            {"name": "Analytic 1", "plan_id": plan.id}
        )

        def add_move(date, amount, distribution):
            move = self.env["account.move"].create(
                {
                    "move_type": "entry",
                    "date": date,
                    "line_ids": [
                        Command.create(
                            {
                                "account_id": self.account100.id,
                                "debit": amount,
                                "analytic_distribution": distribution,
                            }
                        ),
                        Command.create(
                            {
                                "account_id": self.account200.id,
                                "credit": amount,
                                "analytic_distribution": distribution,
                            }
                        ),
                    ],
                }
            )
            move.action_post()

        add_move(self.previous_fy_date_end, 100, {str(analytic.id): 100})
        add_move(self.date_start, 40, {str(analytic.id): 100})
        add_move(self.date_start, 10, False)
        self.env.flush_all()
        company = self.env.user.company_id
        wizard = self.env["trial.balance.report.wizard"].create(
            {
                "date_from": self.date_start,
                "date_to": self.date_end,
                "target_move": "posted",
                "hide_account_at_0": True,
                "company_id": company.id,
                "fy_start_date": self.fy_date_start,
                "grouped_by": "analytic_account",
            }
        )
        res_data = self.env[
            "report.account_financial_report.trial_balance"
        ]._get_report_values(wizard, wizard._prepare_report_data())
        groups = {group["name"]: group for group in res_data["trial_balance_grouped"]}
        self.assertEqual(set(groups), {"Analytic 1", "Without analytic account"})
        analytic_group = groups["Analytic 1"]
        self.assertEqual(analytic_group["type"], "analytic_account_type")
        receivable = next(
            line
            for line in analytic_group["account_data"]
            if line["id"] == self.account100.id
        )
        self.assertEqual(receivable["initial_balance"], 100)
        self.assertEqual(receivable["debit"], 40)
        self.assertEqual(receivable["ending_balance"], 140)
        income = next(
            line
            for line in analytic_group["account_data"]
            if line["id"] == self.account200.id
        )
        self.assertEqual(income["credit"], 40)
        without = next(
            line
            for line in groups["Without analytic account"]["account_data"]
            if line["id"] == self.account100.id
        )
        self.assertEqual(without["debit"], 10)
        self.assertEqual(without["initial_balance"], 0)
