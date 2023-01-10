# © 2016 Julien Coux (Camptocamp)
# © 2018 Forest and Biomass Romania SA
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2021 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class TrialBalanceReport(models.AbstractModel):
    _name = "report.account_financial_report.trial_balance"
    _description = "Trial Balance Report"
    _inherit = "report.account_financial_report.abstract_report"

    def _get_initial_balances_bs_ml_domain(
        self,
        account_ids,
        journal_ids,
        partner_ids,
        company_id,
        date_from,
        only_posted_moves,
        show_partner_details,
    ):
        accounts_domain = [
            ("company_id", "=", company_id),
            ("user_type_id.include_initial_balance", "=", True),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = [("date", "<", date_from)]
        accounts = self.env["account.account"].search(accounts_domain)
        domain += [("account_id", "in", accounts.ids)]
        if company_id:
            domain += [("company_id", "=", company_id)]
        if journal_ids:
            domain += [("journal_id", "in", journal_ids)]
        if partner_ids:
            domain += [("partner_id", "in", partner_ids)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        else:
            domain += [("move_id.state", "in", ["posted", "draft"])]
        if show_partner_details:
            domain += [("account_id.internal_type", "in", ["receivable", "payable"])]
        return domain

    def _get_initial_balances_pl_ml_domain(
        self,
        account_ids,
        journal_ids,
        partner_ids,
        company_id,
        date_from,
        only_posted_moves,
        show_partner_details,
        fy_start_date,
    ):
        accounts_domain = [
            ("company_id", "=", company_id),
            ("user_type_id.include_initial_balance", "=", False),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = [("date", "<", date_from), ("date", ">=", fy_start_date)]
        accounts = self.env["account.account"].search(accounts_domain)
        domain += [("account_id", "in", accounts.ids)]
        if company_id:
            domain += [("company_id", "=", company_id)]
        if journal_ids:
            domain += [("journal_id", "in", journal_ids)]
        if partner_ids:
            domain += [("partner_id", "in", partner_ids)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        else:
            domain += [("move_id.state", "in", ["posted", "draft"])]
        if show_partner_details:
            domain += [("account_id.internal_type", "in", ["receivable", "payable"])]
        return domain

    @api.model
    def _get_period_ml_domain(
        self,
        account_ids,
        journal_ids,
        partner_ids,
        company_id,
        date_to,
        date_from,
        only_posted_moves,
        show_partner_details,
    ):
        domain = [
            ("display_type", "=", False),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
        ]
        if company_id:
            domain += [("company_id", "=", company_id)]
        if account_ids:
            domain += [("account_id", "in", account_ids)]
        if journal_ids:
            domain += [("journal_id", "in", journal_ids)]
        if partner_ids:
            domain += [("partner_id", "in", partner_ids)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        else:
            domain += [("move_id.state", "in", ["posted", "draft"])]
        if show_partner_details:
            domain += [("account_id.internal_type", "in", ["receivable", "payable"])]
        return domain

    def _get_initial_balance_fy_pl_ml_domain(
        self,
        account_ids,
        journal_ids,
        partner_ids,
        company_id,
        fy_start_date,
        only_posted_moves,
        show_partner_details,
    ):
        accounts_domain = [
            ("company_id", "=", company_id),
            ("user_type_id.include_initial_balance", "=", False),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = [("date", "<", fy_start_date)]
        accounts = self.env["account.account"].search(accounts_domain)
        domain += [("account_id", "in", accounts.ids)]
        if company_id:
            domain += [("company_id", "=", company_id)]
        if journal_ids:
            domain += [("journal_id", "in", journal_ids)]
        if partner_ids:
            domain += [("partner_id", "in", partner_ids)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        else:
            domain += [("move_id.state", "in", ["posted", "draft"])]
        if show_partner_details:
            domain += [("account_id.internal_type", "in", ["receivable", "payable"])]
        return domain

    def _get_pl_initial_balance(
        self,
        account_ids,
        journal_ids,
        partner_ids,
        company_id,
        fy_start_date,
        only_posted_moves,
        show_partner_details,
        foreign_currency,
    ):
        domain = self._get_initial_balance_fy_pl_ml_domain(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            fy_start_date,
            only_posted_moves,
            show_partner_details,
        )
        initial_balances = self.env["account.move.line"].read_group(
            domain=domain,
            fields=["account_id", "balance", "amount_currency"],
            groupby=["account_id"],
        )
        pl_initial_balance = 0.0
        pl_initial_currency_balance = 0.0
        for initial_balance in initial_balances:
            pl_initial_balance += initial_balance["balance"]
            if foreign_currency:
                pl_initial_currency_balance += round(
                    initial_balance["amount_currency"], 2
                )
        return pl_initial_balance, pl_initial_currency_balance

    @api.model
    def _compute_account_amount(
        self, total_amount, tb_initial_acc, tb_period_acc, foreign_currency
    ):
        for tb in tb_period_acc:
            acc_id = tb["account_id"][0]
            total_amount[acc_id] = self._prepare_total_amount(tb, foreign_currency)
            total_amount[acc_id]["credit"] = tb["credit"]
            total_amount[acc_id]["debit"] = tb["debit"]
            total_amount[acc_id]["balance"] = tb["balance"]
            total_amount[acc_id]["initial_balance"] = 0.0
        for tb in tb_initial_acc:
            acc_id = tb["account_id"]
            if acc_id not in total_amount.keys():
                total_amount[acc_id] = self._prepare_total_amount(tb, foreign_currency)
            else:
                total_amount[acc_id]["initial_balance"] = tb["balance"]
                total_amount[acc_id]["ending_balance"] += tb["balance"]
                if foreign_currency:
                    total_amount[acc_id]["initial_currency_balance"] = round(
                        tb["amount_currency"], 2
                    )
                    total_amount[acc_id]["ending_currency_balance"] += round(
                        tb["amount_currency"], 2
                    )
        return total_amount

    @api.model
    def _prepare_total_amount(self, tb, foreign_currency):
        res = {
            "credit": 0.0,
            "debit": 0.0,
            "balance": 0.0,
            "initial_balance": tb["balance"],
            "ending_balance": tb["balance"],
        }
        if foreign_currency:
            res["initial_currency_balance"] = round(tb["amount_currency"], 2)
            res["ending_currency_balance"] = round(tb["amount_currency"], 2)
        return res

    @api.model
    def _compute_acc_prt_amount(
        self, total_amount, tb, acc_id, prt_id, foreign_currency
    ):
        # Add keys to dict if not exists
        if acc_id not in total_amount:
            total_amount[acc_id] = self._prepare_total_amount(tb, foreign_currency)
        if prt_id not in total_amount[acc_id]:
            total_amount[acc_id][prt_id] = self._prepare_total_amount(
                tb, foreign_currency
            )
        else:
            # Increase balance field values
            total_amount[acc_id][prt_id]["initial_balance"] = tb["balance"]
            total_amount[acc_id][prt_id]["ending_balance"] += tb["balance"]
            if foreign_currency:
                total_amount[acc_id][prt_id]["initial_currency_balance"] = round(
                    tb["amount_currency"], 2
                )
                total_amount[acc_id][prt_id]["ending_currency_balance"] += round(
                    tb["amount_currency"], 2
                )
        return total_amount

    @api.model
    def _compute_partner_amount(
        self, total_amount, tb_initial_prt, tb_period_prt, foreign_currency
    ):
        partners_ids = set()
        partners_data = {}
        for tb in tb_period_prt:
            acc_id = tb["account_id"][0]
            if tb["partner_id"]:
                prt_id = tb["partner_id"][0]
                if tb["partner_id"] not in partners_ids:
                    partners_data.update(
                        {prt_id: {"id": prt_id, "name": tb["partner_id"][1]}}
                    )
                total_amount[acc_id][prt_id] = self._prepare_total_amount(
                    tb, foreign_currency
                )
                total_amount[acc_id][prt_id]["credit"] = tb["credit"]
                total_amount[acc_id][prt_id]["debit"] = tb["debit"]
                total_amount[acc_id][prt_id]["balance"] = tb["balance"]
                total_amount[acc_id][prt_id]["initial_balance"] = 0.0
                partners_ids.add(tb["partner_id"])
        for tb in tb_initial_prt:
            acc_id = tb["account_id"][0]
            if tb["partner_id"]:
                prt_id = tb["partner_id"][0]
                if tb["partner_id"] not in partners_ids:
                    partners_data.update(
                        {prt_id: {"id": prt_id, "name": tb["partner_id"][1]}}
                    )
                total_amount = self._compute_acc_prt_amount(
                    total_amount, tb, acc_id, prt_id, foreign_currency
                )
        return total_amount, partners_data

    @api.model
    def _get_data(
        self,
        account_ids,
        journal_ids,
        partner_ids,
        company_id,
        date_to,
        date_from,
        foreign_currency,
        only_posted_moves,
        show_partner_details,
        hide_account_at_0,
        unaffected_earnings_account,
        fy_start_date,
    ):
        accounts_domain = [("company_id", "=", company_id)]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
            # If explicit list of accounts is provided,
            # don't include unaffected earnings account
            unaffected_earnings_account = False
        accounts = self.env["account.account"].search(accounts_domain)
        tb_initial_acc = []
        for account in accounts:
            tb_initial_acc.append(
                {"account_id": account.id, "balance": 0.0, "amount_currency": 0.0}
            )
        initial_domain_bs = self._get_initial_balances_bs_ml_domain(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            date_from,
            only_posted_moves,
            show_partner_details,
        )
        tb_initial_acc_bs = self.env["account.move.line"].read_group(
            domain=initial_domain_bs,
            fields=["account_id", "balance", "amount_currency"],
            groupby=["account_id"],
        )
        initial_domain_pl = self._get_initial_balances_pl_ml_domain(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            date_from,
            only_posted_moves,
            show_partner_details,
            fy_start_date,
        )
        tb_initial_acc_pl = self.env["account.move.line"].read_group(
            domain=initial_domain_pl,
            fields=["account_id", "balance", "amount_currency"],
            groupby=["account_id"],
        )
        tb_initial_acc_rg = tb_initial_acc_bs + tb_initial_acc_pl
        for account_rg in tb_initial_acc_rg:
            element = list(
                filter(
                    lambda acc_dict: acc_dict["account_id"]
                    == account_rg["account_id"][0],
                    tb_initial_acc,
                )
            )
            if element:
                element[0]["balance"] += account_rg["balance"]
                element[0]["amount_currency"] += account_rg["amount_currency"]
        if hide_account_at_0:
            tb_initial_acc = [p for p in tb_initial_acc if p["balance"] != 0]

        period_domain = self._get_period_ml_domain(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            date_to,
            date_from,
            only_posted_moves,
            show_partner_details,
        )
        tb_period_acc = self.env["account.move.line"].read_group(
            domain=period_domain,
            fields=["account_id", "debit", "credit", "balance", "amount_currency"],
            groupby=["account_id"],
        )

        if show_partner_details:
            tb_initial_prt_bs = self.env["account.move.line"].read_group(
                domain=initial_domain_bs,
                fields=["account_id", "partner_id", "balance", "amount_currency"],
                groupby=["account_id", "partner_id"],
                lazy=False,
            )
            tb_initial_prt_pl = self.env["account.move.line"].read_group(
                domain=initial_domain_pl,
                fields=["account_id", "partner_id", "balance", "amount_currency"],
                groupby=["account_id", "partner_id"],
            )
            tb_initial_prt = tb_initial_prt_bs + tb_initial_prt_pl
            if hide_account_at_0:
                tb_initial_prt = [p for p in tb_initial_prt if p["balance"] != 0]
            tb_period_prt = self.env["account.move.line"].read_group(
                domain=period_domain,
                fields=[
                    "account_id",
                    "partner_id",
                    "debit",
                    "credit",
                    "balance",
                    "amount_currency",
                ],
                groupby=["account_id", "partner_id"],
                lazy=False,
            )
        total_amount = {}
        partners_data = []
        total_amount = self._compute_account_amount(
            total_amount, tb_initial_acc, tb_period_acc, foreign_currency
        )
        if show_partner_details:
            total_amount, partners_data = self._compute_partner_amount(
                total_amount, tb_initial_prt, tb_period_prt, foreign_currency
            )
        accounts_ids = list(total_amount.keys())
        unaffected_id = unaffected_earnings_account
        if unaffected_id:
            if unaffected_id not in accounts_ids:
                accounts_ids.append(unaffected_id)
                total_amount[unaffected_id] = {}
                total_amount[unaffected_id]["initial_balance"] = 0.0
                total_amount[unaffected_id]["balance"] = 0.0
                total_amount[unaffected_id]["credit"] = 0.0
                total_amount[unaffected_id]["debit"] = 0.0
                total_amount[unaffected_id]["ending_balance"] = 0.0
                if foreign_currency:
                    total_amount[unaffected_id]["initial_currency_balance"] = 0.0
                    total_amount[unaffected_id]["ending_currency_balance"] = 0.0
        accounts_data = self._get_accounts_data(accounts_ids)
        (
            pl_initial_balance,
            pl_initial_currency_balance,
        ) = self._get_pl_initial_balance(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            fy_start_date,
            only_posted_moves,
            show_partner_details,
            foreign_currency,
        )
        if unaffected_id:
            total_amount[unaffected_id]["ending_balance"] += pl_initial_balance
            total_amount[unaffected_id]["initial_balance"] += pl_initial_balance
            if foreign_currency:
                total_amount[unaffected_id][
                    "ending_currency_balance"
                ] += pl_initial_currency_balance
                total_amount[unaffected_id][
                    "initial_currency_balance"
                ] += pl_initial_currency_balance
        return total_amount, accounts_data, partners_data

    def _get_hierarchy_groups(
        self, group_ids, groups_data, old_groups_ids, foreign_currency
    ):
        new_parents = False
        for group_id in group_ids:
            if groups_data[group_id]["parent_id"]:
                new_parents = True
                nw_id = groups_data[group_id]["parent_id"]
                if nw_id in groups_data.keys():
                    groups_data[nw_id]["initial_balance"] += groups_data[group_id][
                        "initial_balance"
                    ]
                    groups_data[nw_id]["debit"] += groups_data[group_id]["debit"]
                    groups_data[nw_id]["credit"] += groups_data[group_id]["credit"]
                    groups_data[nw_id]["balance"] += groups_data[group_id]["balance"]
                    groups_data[nw_id]["ending_balance"] += groups_data[group_id][
                        "ending_balance"
                    ]
                    if foreign_currency:
                        groups_data[nw_id]["initial_currency_balance"] += groups_data[
                            group_id
                        ]["initial_currency_balance"]
                        groups_data[nw_id]["ending_currency_balance"] += groups_data[
                            group_id
                        ]["ending_currency_balance"]
                else:
                    groups_data[nw_id] = {}
                    groups_data[nw_id]["initial_balance"] = groups_data[group_id][
                        "initial_balance"
                    ]
                    groups_data[nw_id]["debit"] = groups_data[group_id]["debit"]
                    groups_data[nw_id]["credit"] = groups_data[group_id]["credit"]
                    groups_data[nw_id]["balance"] = groups_data[group_id]["balance"]
                    groups_data[nw_id]["ending_balance"] = groups_data[group_id][
                        "ending_balance"
                    ]
                    if foreign_currency:
                        groups_data[nw_id]["initial_currency_balance"] = groups_data[
                            group_id
                        ]["initial_currency_balance"]
                        groups_data[nw_id]["ending_currency_balance"] = groups_data[
                            group_id
                        ]["ending_currency_balance"]
        if new_parents:
            nw_groups_ids = []
            for group_id in list(groups_data.keys()):
                if group_id not in old_groups_ids:
                    nw_groups_ids.append(group_id)
                    old_groups_ids.append(group_id)
            groups = self.env["account.group"].browse(nw_groups_ids)
            for group in groups:
                groups_data[group.id].update(
                    {
                        "id": group.id,
                        "code": group.code_prefix,
                        "name": group.name,
                        "parent_id": group.parent_id.id,
                        "parent_path": group.parent_path,
                        "complete_code": group.complete_code,
                        "account_ids": group.compute_account_ids.ids,
                        "type": "group_type",
                    }
                )
            groups_data = self._get_hierarchy_groups(
                nw_groups_ids, groups_data, old_groups_ids, foreign_currency
            )
        return groups_data

    def _get_groups_data(self, accounts_data, total_amount, foreign_currency):
        accounts_ids = list(accounts_data.keys())
        accounts = self.env["account.account"].browse(accounts_ids)
        account_group_relation = {}
        for account in accounts:
            accounts_data[account.id]["complete_code"] = (
                account.group_id.complete_code if account.group_id.id else ""
            )
            if account.group_id.id:
                if account.group_id.id not in account_group_relation.keys():
                    account_group_relation.update({account.group_id.id: [account.id]})
                else:
                    account_group_relation[account.group_id.id].append(account.id)
        groups = self.env["account.group"].browse(account_group_relation.keys())
        groups_data = {}
        for group in groups:
            groups_data.update(
                {
                    group.id: {
                        "id": group.id,
                        "code": group.code_prefix,
                        "name": group.name,
                        "parent_id": group.parent_id.id,
                        "parent_path": group.parent_path,
                        "type": "group_type",
                        "complete_code": group.complete_code,
                        "account_ids": group.compute_account_ids.ids,
                        "initial_balance": 0.0,
                        "credit": 0.0,
                        "debit": 0.0,
                        "balance": 0.0,
                        "ending_balance": 0.0,
                    }
                }
            )
            if foreign_currency:
                groups_data[group.id]["initial_currency_balance"] = 0.0
                groups_data[group.id]["ending_currency_balance"] = 0.0
        for group_id in account_group_relation.keys():
            for account_id in account_group_relation[group_id]:
                groups_data[group_id]["initial_balance"] += total_amount[account_id][
                    "initial_balance"
                ]
                groups_data[group_id]["debit"] += total_amount[account_id]["debit"]
                groups_data[group_id]["credit"] += total_amount[account_id]["credit"]
                groups_data[group_id]["balance"] += total_amount[account_id]["balance"]
                groups_data[group_id]["ending_balance"] += total_amount[account_id][
                    "ending_balance"
                ]
                if foreign_currency:
                    groups_data[group_id]["initial_currency_balance"] += total_amount[
                        account_id
                    ]["initial_currency_balance"]
                    groups_data[group_id]["ending_currency_balance"] += total_amount[
                        account_id
                    ]["ending_currency_balance"]
        group_ids = list(groups_data.keys())
        old_group_ids = list(groups_data.keys())
        groups_data = self._get_hierarchy_groups(
            group_ids, groups_data, old_group_ids, foreign_currency
        )
        return groups_data

    @api.model
    def _get_computed_account_groups(self, account_code, data, groups):
        show_hierarchy_level = data["show_hierarchy_level"]
        limit_hierarchy_level = data["limit_hierarchy_level"]
        account_groups = []
        if limit_hierarchy_level:
            limit_level = show_hierarchy_level
        else:
            limit_level = len(account_code)
        for i in range(limit_level + 1):
            group_code = account_code[:i]
            group = groups.filtered(lambda g: g.code_prefix == group_code)[:1]
            # Only append existing groups if not limit_hierarchy_level
            if limit_hierarchy_level or group:
                account_groups.append((group_code, group))
        return account_groups

    def _get_computed_groups_data(
        self, accounts_data, total_amount, foreign_currency, data
    ):
        show_hierarchy_level = data["show_hierarchy_level"]
        hide_parent_hierarchy_level = data["hide_parent_hierarchy_level"]
        groups = self.env["account.group"].search([])
        groups_data = {
            "": {
                "id": False,
                "code": "",
                "name": "Total",
                "parent_id": False,
                "parent_path": "",
                "level": show_hierarchy_level if hide_parent_hierarchy_level else 0,
                "type": "group_type",
                "complete_code": "",
                "account_ids": [],
                "initial_balance": 0.0,
                "debit": 0.0,
                "credit": 0.0,
                "balance": 0.0,
                "ending_balance": 0.0,
            }
        }
        if foreign_currency:
            groups_data[""].update(
                {"initial_currency_balance": 0.0, "ending_currency_balance": 0.0}
            )
        for account in accounts_data.values():
            previous_group = False
            for group_code, group in self._get_computed_account_groups(
                account["code"], data, groups
            ):
                if group_code and not group and not previous_group:
                    raise ValidationError(
                        _("Code %s can not be related with any account group")
                        % group_code
                    )
                acc_id = account["id"]
                if group_code not in groups_data:
                    len_group = len(group_code)
                    groups_data[group_code] = {
                        "id": group.id if group else previous_group.id,
                        "code": group_code,
                        "name": group.name
                        if group
                        else "{} ({})".format(previous_group.name, group_code),
                        "parent_id": group.parent_id.id if group else previous_group.id,
                        "parent_path": group.parent_path
                        if group
                        else previous_group.parent_path,
                        "level": len_group,
                        "type": "group_type",
                        "complete_code": "/".join(
                            [group_code[:i] for i in range(1, len_group)]
                        ),
                        "account_ids": [account["id"]],
                        "initial_balance": total_amount[acc_id]["initial_balance"],
                        "debit": total_amount[acc_id]["debit"],
                        "credit": total_amount[acc_id]["credit"],
                        "balance": total_amount[acc_id]["balance"],
                        "ending_balance": total_amount[acc_id]["ending_balance"],
                    }
                    if foreign_currency:
                        groups_data[group_code].update(
                            {
                                "initial_currency_balance": total_amount[acc_id][
                                    "initial_currency_balance"
                                ],
                                "ending_currency_balance": total_amount[acc_id][
                                    "ending_currency_balance"
                                ],
                            }
                        )
                else:
                    groups_data[group_code]["account_ids"].append(acc_id)
                    groups_data[group_code]["initial_balance"] += total_amount[acc_id][
                        "initial_balance"
                    ]
                    groups_data[group_code]["debit"] += total_amount[acc_id]["debit"]
                    groups_data[group_code]["credit"] += total_amount[acc_id]["credit"]
                    groups_data[group_code]["balance"] += total_amount[acc_id][
                        "balance"
                    ]
                    groups_data[group_code]["ending_balance"] += total_amount[acc_id][
                        "ending_balance"
                    ]
                    if foreign_currency:
                        groups_data[group_code][
                            "initial_currency_balance"
                        ] += total_amount[acc_id]["initial_currency_balance"]
                        groups_data[group_code][
                            "ending_currency_balance"
                        ] += total_amount[acc_id]["ending_currency_balance"]
                if group:
                    previous_group = group
        return groups_data

    def _get_report_values(self, docids, data):
        show_partner_details = data["show_partner_details"]
        wizard_id = data["wizard_id"]
        company = self.env["res.company"].browse(data["company_id"])
        company_id = data["company_id"]
        partner_ids = data["partner_ids"]
        journal_ids = data["journal_ids"]
        account_ids = data["account_ids"]
        date_to = data["date_to"]
        date_from = data["date_from"]
        hide_account_at_0 = data["hide_account_at_0"]
        hierarchy_on = data["hierarchy_on"]
        limit_hierarchy_level = data["limit_hierarchy_level"]
        show_hierarchy_level = data["show_hierarchy_level"]
        foreign_currency = data["foreign_currency"]
        only_posted_moves = data["only_posted_moves"]
        unaffected_earnings_account = data["unaffected_earnings_account"]
        fy_start_date = data["fy_start_date"]
        total_amount, accounts_data, partners_data = self._get_data(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            date_to,
            date_from,
            foreign_currency,
            only_posted_moves,
            show_partner_details,
            hide_account_at_0,
            unaffected_earnings_account,
            fy_start_date,
        )
        trial_balance = []
        if not show_partner_details:
            for account_id in accounts_data.keys():
                accounts_data[account_id].update(
                    {
                        "initial_balance": total_amount[account_id]["initial_balance"],
                        "credit": total_amount[account_id]["credit"],
                        "debit": total_amount[account_id]["debit"],
                        "balance": total_amount[account_id]["balance"],
                        "ending_balance": total_amount[account_id]["ending_balance"],
                        "type": "account_type",
                    }
                )
                if foreign_currency:
                    accounts_data[account_id].update(
                        {
                            "ending_currency_balance": total_amount[account_id][
                                "ending_currency_balance"
                            ],
                            "initial_currency_balance": total_amount[account_id][
                                "initial_currency_balance"
                            ],
                        }
                    )
            if hierarchy_on == "relation":
                groups_data = self._get_groups_data(
                    accounts_data, total_amount, foreign_currency
                )
                trial_balance = list(groups_data.values())
                trial_balance += list(accounts_data.values())
                trial_balance = sorted(trial_balance, key=lambda k: k["complete_code"])
                for trial in trial_balance:
                    counter = trial["complete_code"].count("/")
                    trial["level"] = counter
            if hierarchy_on == "computed":
                groups_data = self._get_computed_groups_data(
                    accounts_data, total_amount, foreign_currency, data
                )
                trial_balance = list(groups_data.values())
                if not limit_hierarchy_level:
                    trial_balance += list(accounts_data.values())
                trial_balance = sorted(trial_balance, key=lambda k: k["code"])
            if hierarchy_on == "none":
                trial_balance = list(accounts_data.values())
                trial_balance = sorted(trial_balance, key=lambda k: k["code"])
        else:
            if foreign_currency:
                for account_id in accounts_data.keys():
                    total_amount[account_id]["currency_id"] = accounts_data[account_id][
                        "currency_id"
                    ]
                    total_amount[account_id]["currency_name"] = accounts_data[
                        account_id
                    ]["currency_name"]
        return {
            "doc_ids": [wizard_id],
            "doc_model": "trial.balance.report.wizard",
            "docs": self.env["trial.balance.report.wizard"].browse(wizard_id),
            "foreign_currency": data["foreign_currency"],
            "company_name": company.display_name,
            "company_currency": company.currency_id,
            "currency_name": company.currency_id.name,
            "date_from": data["date_from"],
            "date_to": data["date_to"],
            "only_posted_moves": data["only_posted_moves"],
            "hide_account_at_0": data["hide_account_at_0"],
            "show_partner_details": data["show_partner_details"],
            "limit_hierarchy_level": data["limit_hierarchy_level"],
            "hierarchy_on": hierarchy_on,
            "trial_balance": trial_balance,
            "total_amount": total_amount,
            "accounts_data": accounts_data,
            "partners_data": partners_data,
            "show_hierarchy_level": show_hierarchy_level,
        }
