# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestTrialBalanceReport(common.TransactionCase):
    def setUp(self):
        super(TestTrialBalanceReport, self).setUp()
        group_obj = self.env["account.group"]
        acc_obj = self.env["account.account"]
        self.group1 = group_obj.create({"code_prefix_start": "1", "name": "Group 1"})
        self.group11 = group_obj.create(
            {"code_prefix_start": "11", "name": "Group 11", "parent_id": self.group1.id}
        )
        self.group2 = group_obj.create({"code_prefix_start": "2", "name": "Group 2"})
        self.account100 = acc_obj.create(
            {
                "code": "100",
                "name": "Account 100",
                "group_id": self.group1.id,
                "user_type_id": self.env.ref("account.data_account_type_receivable").id,
                "reconcile": True,
            }
        )
        self.account110 = self.env["account.account"].search(
            [
                (
                    "user_type_id",
                    "=",
                    self.env.ref("account.data_unaffected_earnings").id,
                )
            ],
            limit=1,
        )
        self.account200 = acc_obj.create(
            {
                "code": "200",
                "name": "Account 200",
                "group_id": self.group2.id,
                "user_type_id": self.env.ref(
                    "account.data_account_type_other_income"
                ).id,
            }
        )
        self.account300 = acc_obj.create(
            {
                "code": "300",
                "name": "Account 300",
                "user_type_id": self.env.ref(
                    "account.data_account_type_other_income"
                ).id,
            }
        )
        self.account301 = acc_obj.create(
            {
                "code": "301",
                "name": "Account 301",
                "group_id": self.group2.id,
                "user_type_id": self.env.ref(
                    "account.data_account_type_other_income"
                ).id,
            }
        )
        self.previous_fy_date_start = "2015-01-01"
        self.previous_fy_date_end = "2015-12-31"
        self.fy_date_start = "2016-01-01"
        self.fy_date_end = "2016-12-31"
        self.date_start = "2016-01-01"
        self.date_end = "2016-12-31"
        self.partner = self.env.ref("base.res_partner_12")
        self.unaffected_account = self.env["account.account"].search(
            [
                (
                    "user_type_id",
                    "=",
                    self.env.ref("account.data_unaffected_earnings").id,
                )
            ],
            limit=1,
        )

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
        journal = self.env["account.journal"].search([], limit=1)
        partner = self.env.ref("base.res_partner_12")
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
                        "account_id": self.account301.id,
                    },
                ),
            ],
        }
        move = self.env["account.move"].create(move_vals)
        move.action_post()

    def _get_report_lines(self, with_partners=False, hierarchy_on="computed"):
        company = self.env.ref("base.main_company")
        trial_balance = self.env["trial.balance.report.wizard"].create(
            {
                "date_from": self.date_start,
                "date_to": self.date_end,
                "target_move": "posted",
                "hide_account_at_0": True,
                "hierarchy_on": hierarchy_on,
                "company_id": company.id,
                "fy_start_date": self.fy_date_start,
                "show_partner_details": with_partners,
            }
        )
        data = trial_balance._prepare_report_trial_balance()
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
        partner_in_report = False
        if account_id in total_amount.keys():
            if partner_id in total_amount[account_id]:
                partner_in_report = True
        return partner_in_report

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
                for key in account.keys():
                    if key == feature:
                        total += account[key]
        return total

    def test_00_account_group(self):
        self.assertTrue(self.account100 in self.group1.compute_account_ids)
        self.assertTrue(self.account200 in self.group2.compute_account_ids)

    def test_01_account_balance_computed(self):
        # Make sure there's no account of type "Current Year Earnings" in the
        # groups - We change the code
        earning_accs = self.env["account.account"].search(
            [("user_type_id", "=", self.env.ref("account.data_unaffected_earnings").id)]
        )
        for acc in earning_accs:
            if acc.code.startswith("1") or acc.code.startswith("2"):
                acc.code = "999" + acc.code
        # Generate the general ledger line
        res_data = self._get_report_lines()
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
        res_data = self._get_report_lines()
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

        # Add reversed move of the initial move the first day of fiscal year
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
        res_data = self._get_report_lines()
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
        self.assertEqual(group2_lines["debit"], 1000)
        self.assertEqual(group2_lines["credit"], 0)
        self.assertEqual(group2_lines["final_balance"], 1000)

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
        res_data = self._get_report_lines()
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
        self.assertEqual(group2_lines["debit"], 2000)
        self.assertEqual(group2_lines["credit"], 0)
        self.assertEqual(group2_lines["final_balance"], 2000)

    def test_02_account_balance_hierarchy(self):
        # Generate the general ledger line
        res_data = self._get_report_lines(hierarchy_on="relation")
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
        res_data = self._get_report_lines(hierarchy_on="relation")
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
        res_data = self._get_report_lines(hierarchy_on="relation")
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
        res_data = self._get_report_lines(hierarchy_on="relation")
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
        journal = self.env["account.journal"].search([], limit=1)
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
        company = self.env.ref("base.main_company")
        trial_balance = self.env["trial.balance.report.wizard"].create(
            {
                "date_from": self.date_start,
                "date_to": self.date_end,
                "target_move": "posted",
                "hide_account_at_0": False,
                "hierarchy_on": "none",
                "company_id": company.id,
                "fy_start_date": self.fy_date_start,
            }
        )
        data = trial_balance._prepare_report_trial_balance()
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
        journal = self.env["account.journal"].search([], limit=1)
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
                "hierarchy_on": "none",
                "company_id": company.id,
                "fy_start_date": self.fy_date_start,
            }
        )
        data = trial_balance._prepare_report_trial_balance()
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
        journal = self.env["account.journal"].search([], limit=1)
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
                "hierarchy_on": "none",
                "company_id": company.id,
                "fy_start_date": self.fy_date_start,
            }
        )
        data = trial_balance._prepare_report_trial_balance()
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
