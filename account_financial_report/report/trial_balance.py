# © 2016 Julien Coux (Camptocamp)
# © 2018 Forest and Biomass Romania SA
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import unicodedata

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero


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
            ("company_ids", "in", [company_id]),
            ("include_initial_balance", "=", True),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = [("date", "<", date_from)]
        accounts = (
            self.env["account.account"]
            .with_context(active_test=False)
            .search(accounts_domain)
        )
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
            domain += [
                (
                    "account_id.account_type",
                    "in",
                    ["asset_receivable", "liability_payable"],
                )
            ]
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
            ("company_ids", "in", [company_id]),
            ("include_initial_balance", "=", False),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = [("date", "<", date_from), ("date", ">=", fy_start_date)]
        accounts = (
            self.env["account.account"]
            .with_context(active_test=False)
            .search(accounts_domain)
        )
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
            domain += [
                (
                    "account_id.account_type",
                    "in",
                    ["asset_receivable", "liability_payable"],
                )
            ]
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
            ("display_type", "not in", ["line_note", "line_section"]),
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
            domain += [
                (
                    "account_id.account_type",
                    "in",
                    ["asset_receivable", "liability_payable"],
                )
            ]
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
            ("company_ids", "in", [company_id]),
            ("include_initial_balance", "=", False),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = [("date", "<", fy_start_date)]
        accounts = (
            self.env["account.account"]
            .with_context(active_test=False)
            .search(accounts_domain)
        )
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
            domain += [
                (
                    "account_id.account_type",
                    "in",
                    ["asset_receivable", "liability_payable"],
                )
            ]
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
        [(balance, amount_currency)] = self.env["account.move.line"]._read_group(
            domain, [], ["balance:sum", "amount_currency:sum"]
        )
        currency_balance = round(amount_currency or 0.0, 2) if foreign_currency else 0.0
        return balance or 0.0, currency_balance

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
    def _get_empty_amounts(self, foreign_currency):
        return self._prepare_total_amount(
            {"balance": 0.0, "amount_currency": 0.0}, foreign_currency
        )

    @api.model
    def _read_ml_totals(self, domain, groupby, period=False):
        """Sum the journal items of ``domain`` in a single query.

        Each returned tuple holds the ``groupby`` records followed by the sums
        of balance and amount in currency, and of debit and credit when
        ``period`` is set. ``_read_group`` is used instead of ``read_group``
        because the latter hides ``amount_currency`` unless the lines are
        also grouped by currency, which used to need an extra query per
        account.
        """
        aggregates = ["balance:sum", "amount_currency:sum"]
        if period:
            aggregates += ["debit:sum", "credit:sum"]
        return self.env["account.move.line"]._read_group(domain, groupby, aggregates)

    @api.model
    def _add_ml_totals(self, amounts, totals, initial, foreign_currency):
        """Add the sums returned by ``_read_ml_totals`` to ``amounts``."""
        balance, amount_currency = totals[0], totals[1]
        amounts["ending_balance"] += balance
        if initial:
            amounts["initial_balance"] += balance
        else:
            amounts["balance"] += balance
            amounts["debit"] += totals[2]
            amounts["credit"] += totals[3]
        if foreign_currency:
            amounts["ending_currency_balance"] += amount_currency
            if initial:
                amounts["initial_currency_balance"] += amount_currency

    @api.model
    def _partner_sort_key(self, partner_id, name):
        """Alphabetical order ignoring case and accents, missing partner last."""
        normalized = "".join(
            char
            for char in unicodedata.normalize("NFKD", str(name))
            if not unicodedata.combining(char)
        ).casefold()
        return (not partner_id, normalized, partner_id)

    @api.model
    def _get_amount_domains(
        self,
        account_ids,
        journal_ids,
        partner_ids,
        company_id,
        date_to,
        date_from,
        only_posted_moves,
        fy_start_date,
        show_partner_details,
    ):
        """Return ``(domain, is initial balance)`` for the amount columns.

        With ``show_partner_details``, the domain hooks restrict the lines to
        receivable and payable accounts.
        """
        args = (account_ids, journal_ids, partner_ids, company_id)
        return [
            (
                self._get_initial_balances_bs_ml_domain(
                    *args, date_from, only_posted_moves, show_partner_details
                ),
                True,
            ),
            (
                self._get_initial_balances_pl_ml_domain(
                    *args,
                    date_from,
                    only_posted_moves,
                    show_partner_details,
                    fy_start_date,
                ),
                True,
            ),
            (
                self._get_period_ml_domain(
                    *args, date_to, date_from, only_posted_moves, show_partner_details
                ),
                False,
            ),
        ]

    @api.model
    def _sum_account_amounts(self, total_amount, domains, foreign_currency):
        for domain, initial in domains:
            for account, *totals in self._read_ml_totals(
                domain, ["account_id"], period=not initial
            ):
                amounts = total_amount.setdefault(
                    account.id, self._get_empty_amounts(foreign_currency)
                )
                self._add_ml_totals(amounts, totals, initial, foreign_currency)

    @api.model
    def _sum_analytic_amounts(self, total_amount, domains, foreign_currency):
        """Amounts of each account by analytic account in ``group_by_data``.

        A line with several analytic accounts is counted in each of them, so
        these amounts never feed the account totals.
        """
        # Grouping by a many2many does not flush it: the analytic accounts of
        # the lines are a stored compute that may still be pending.
        self.env["account.move.line"].flush_model(["analytic_account_ids"])
        for domain, initial in domains:
            for account, analytic, *totals in self._read_ml_totals(
                domain, ["account_id", "analytic_account_ids"], period=not initial
            ):
                gb_data = total_amount[account.id].setdefault("group_by_data", {})
                amounts = gb_data.setdefault(
                    analytic.id or 0, self._get_empty_amounts(foreign_currency)
                )
                self._add_ml_totals(amounts, totals, initial, foreign_currency)
        for amounts in total_amount.values():
            amounts["group_by"] = "analytic_account_ids"
            amounts.setdefault(
                "group_by_data", {0: self._get_empty_amounts(foreign_currency)}
            )

    @api.model
    def _sum_partner_amounts(self, total_amount, domains, foreign_currency):
        """Add the amounts by partner id (0 without partner) to each account."""
        partners_data = {}
        for domain, initial in domains:
            for account, partner, *totals in self._read_ml_totals(
                domain, ["account_id", "partner_id"], period=not initial
            ):
                prt_id = partner.id or 0
                if prt_id not in partners_data:
                    partners_data[prt_id] = {
                        "id": prt_id,
                        "name": partner.name or _("Missing Partner"),
                    }
                acc_amounts = total_amount[account.id]
                if prt_id not in acc_amounts:
                    acc_amounts[prt_id] = self._get_empty_amounts(foreign_currency)
                    acc_amounts[prt_id]["partner_name"] = partners_data[prt_id]["name"]
                self._add_ml_totals(
                    acc_amounts[prt_id], totals, initial, foreign_currency
                )
        return partners_data

    @api.model
    def _remove_lone_missing_partner(self, total_amount):
        """Without any partner to show, the lines without partner are the
        whole account: drop that row so the account looks like the others."""
        for acc_amounts in total_amount.values():
            partner_keys = [key for key in acc_amounts if isinstance(key, int)]
            if partner_keys == [0]:
                del acc_amounts[0]

    @api.model
    def _round_currency_amounts(self, total_amount):
        for amounts in total_amount.values():
            items = [amounts]
            items += [value for key, value in amounts.items() if isinstance(key, int)]
            for item in items:
                for key in ("initial_currency_balance", "ending_currency_balance"):
                    item[key] = round(item[key], 2)

    @api.model
    def _sort_total_amount(self, total_amount, accounts_data):
        """Accounts by code, and partners alphabetically inside each account."""
        sorted_total_amount = {}
        for acc_id in sorted(total_amount, key=lambda a: accounts_data[a]["code"]):
            acc_amounts = total_amount[acc_id]
            sorted_total_amount[acc_id] = {
                key: value
                for key, value in acc_amounts.items()
                if not isinstance(key, int)
            }
            partner_keys = sorted(
                (key for key in acc_amounts if isinstance(key, int)),
                key=lambda key: self._partner_sort_key(
                    key, acc_amounts[key]["partner_name"]
                ),
            )
            for key in partner_keys:
                sorted_total_amount[acc_id][key] = acc_amounts[key]
        return sorted_total_amount

    def _remove_accounts_at_cero(self, total_amount, show_partner_details, company):
        def is_removable(d):
            rounding = company.currency_id.rounding
            return (
                float_is_zero(d["initial_balance"], precision_rounding=rounding)
                and float_is_zero(d["credit"], precision_rounding=rounding)
                and float_is_zero(d["debit"], precision_rounding=rounding)
                and float_is_zero(d["ending_balance"], precision_rounding=rounding)
            )

        accounts_to_remove = []
        for acc_id, ta_data in total_amount.items():
            if show_partner_details:
                # The partner data is in the same account data dict but with
                # the partner id as the key
                partner_to_remove = [
                    key
                    for key, value in ta_data.items()
                    if isinstance(key, int) and is_removable(value)
                ]
                for partner_id in partner_to_remove:
                    del ta_data[partner_id]
            # An account at 0 is still shown when some of its partners are
            # not, e.g. an amount posted to the wrong partner.
            if is_removable(ta_data) and not any(
                isinstance(key, int) for key in ta_data
            ):
                accounts_to_remove.append(acc_id)
        for account_id in accounts_to_remove:
            del total_amount[account_id]

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
        grouped_by,
    ):
        """Return the totals of every account, by code.

        ``total_amount`` maps each account id to its amounts. With
        ``show_partner_details``, receivable and payable accounts also hold
        one entry per partner id (0 for the lines without partner), sorted
        alphabetically; every other account keeps its own totals only. With
        ``grouped_by``, ``group_by_data`` holds the amounts by analytic
        account (0 for the lines without one).
        """
        accounts_domain = [("company_ids", "in", [company_id])]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
            # If explicit list of accounts is provided,
            # don't include unaffected earnings account
            unaffected_earnings_account = False
        accounts = (
            self.env["account.account"]
            .with_context(active_test=False)
            .search(accounts_domain)
        )
        total_amount = {
            account.id: self._get_empty_amounts(foreign_currency)
            for account in accounts
        }

        domains = self._get_amount_domains(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            date_to,
            date_from,
            only_posted_moves,
            fy_start_date,
            False,
        )
        self._sum_account_amounts(total_amount, domains, foreign_currency)
        if grouped_by:
            self._sum_analytic_amounts(total_amount, domains, foreign_currency)
        partners_data = {}
        if show_partner_details:
            partner_domains = self._get_amount_domains(
                account_ids,
                journal_ids,
                partner_ids,
                company_id,
                date_to,
                date_from,
                only_posted_moves,
                fy_start_date,
                True,
            )
            partners_data = self._sum_partner_amounts(
                total_amount, partner_domains, foreign_currency
            )
        if foreign_currency:
            self._round_currency_amounts(total_amount)
        # Remove accounts a 0 from collections
        if hide_account_at_0:
            company = self.env["res.company"].browse(company_id)
            self._remove_accounts_at_cero(total_amount, show_partner_details, company)
        if show_partner_details:
            self._remove_lone_missing_partner(total_amount)

        accounts_ids = list(total_amount.keys())
        unaffected_id = unaffected_earnings_account
        if unaffected_id:
            if unaffected_id not in accounts_ids:
                accounts_ids.append(unaffected_id)
                total_amount[unaffected_id] = self._get_empty_amounts(foreign_currency)
            if grouped_by:
                total_amount[unaffected_id]["group_by"] = "analytic_account_ids"
                total_amount[unaffected_id]["group_by_data"] = {
                    0: self._get_empty_amounts(foreign_currency)
                }
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
            False,
            foreign_currency,
        )
        if unaffected_id:
            total_amount[unaffected_id]["ending_balance"] += pl_initial_balance
            total_amount[unaffected_id]["initial_balance"] += pl_initial_balance
            if foreign_currency:
                total_amount[unaffected_id]["ending_currency_balance"] += (
                    pl_initial_currency_balance
                )
                total_amount[unaffected_id]["initial_currency_balance"] += (
                    pl_initial_currency_balance
                )
            if grouped_by:
                unaffected_amounts = total_amount[unaffected_id]
                unaffected_amounts["group_by_data"][0].update(
                    {
                        key: unaffected_amounts[key]
                        for key in unaffected_amounts["group_by_data"][0]
                    }
                )
        total_amount = self._sort_total_amount(total_amount, accounts_data)
        return total_amount, accounts_data, partners_data

    def _get_data_grouped(self, total_amount, accounts_data, foreign_currency):
        """Get the data grouped by analytical account instead of as used
        "without grouping".
        """
        trial_balance = {}
        total_amount_grouped = {"type": "total", "name": _("TOTAL")}
        f_names = [
            "credit",
            "debit",
            "balance",
            "initial_balance",
            "ending_balance",
            "initial_currency_balance",
            "ending_currency_balance",
        ]
        for f_name in f_names:
            total_amount_grouped[f_name] = 0
        for a_id in list(total_amount.keys()):
            for key in list(total_amount[a_id]["group_by_data"].keys()):
                total_amount_item2 = total_amount[a_id]["group_by_data"][key]
                if key not in trial_balance:
                    trial_balance[key] = {}
                    for f_name in f_names:
                        if f_name in total_amount_item2:
                            trial_balance[key][f_name] = 0
                    trial_balance[key]["account_data"] = {}
                for f_name in f_names:
                    if f_name in total_amount_item2:
                        trial_balance[key][f_name] += total_amount_item2[f_name]
                # Prepare data_item
                data_item = total_amount_item2
                data_item["type"] = "account_type"
                data_item["id"] = a_id
                data_item["name"] = accounts_data[a_id]["name"]
                data_item["code"] = accounts_data[a_id]["code"]
                data_item["aml_domain"] = accounts_data[a_id].get("aml_domain")
                data_item["pl_domain"] = accounts_data[a_id].get("pl_domain")
                if foreign_currency:
                    data_item["currency_id"] = accounts_data[a_id]["currency_id"]
                    data_item["currency_name"] = accounts_data[a_id]["currency_name"]
                trial_balance[key]["account_data"][a_id] = data_item
        analytic_account_ids = list(trial_balance.keys())
        aa_data = {}
        aaa_model = self.env["account.analytic.account"].with_context(active_test=False)
        analytic_accounts = aaa_model.search_read(
            domain=[("id", "in", analytic_account_ids)],
            fields=["display_name"],
        )
        for aa in analytic_accounts:
            aa_data[aa["id"]] = aa
        for aa_id in analytic_account_ids:
            trial_balance[aa_id]["id"] = aa_id
            trial_balance[aa_id]["type"] = "analytic_account_type"
            trial_balance[aa_id]["name"] = (
                aa_data[aa_id]["display_name"]
                if aa_id in aa_data
                else _("Without analytic account")
            )
            account_data_item = list(trial_balance[aa_id]["account_data"].values())
            account_data_item = sorted(account_data_item, key=lambda k: k["code"])
            trial_balance[aa_id]["account_data"] = account_data_item
            for f_name in f_names:
                if f_name in trial_balance[aa_id]:
                    total_amount_grouped[f_name] += trial_balance[aa_id][f_name]
        trial_balance = list(trial_balance.values())
        trial_balance = sorted(trial_balance, key=lambda k: k["name"])
        return trial_balance, total_amount_grouped

    def _get_hierarchy_groups(self, group_ids, groups_data, foreign_currency):
        processed_groups = []
        # Sort groups so that parent groups are processed before child groups
        groups = (
            self.env["account.group"]
            .browse(group_ids)
            .sorted(key=lambda x: x.complete_code)
        )
        for group in groups:
            group_id = group.id
            parent_id = groups_data[group_id]["parent_id"]
            if group_id in processed_groups:
                raise UserError(
                    _(
                        "There is a problem in the structure of the account groups. "
                        "You may need to create some child group of %s."
                    )
                    % groups_data[group_id]["name"]
                )
            else:
                processed_groups.append(parent_id)
            while parent_id:
                if parent_id not in groups_data.keys():
                    group = self.env["account.group"].browse(parent_id)
                    groups_data[group.id] = {
                        "id": group.id,
                        "code": group.code_prefix_start,
                        "name": group.name,
                        "parent_id": group.parent_id.id,
                        "complete_code": group.complete_code,
                        "account_ids": [],
                        "type": "group_type",
                        "initial_balance": 0,
                        "debit": 0,
                        "credit": 0,
                        "balance": 0,
                        "ending_balance": 0,
                    }
                    if foreign_currency:
                        groups_data[group.id].update(
                            initial_currency_balance=0,
                            ending_currency_balance=0,
                        )
                acc_keys = ["debit", "credit", "balance"]
                acc_keys += ["initial_balance", "ending_balance"]
                for acc_key in acc_keys:
                    groups_data[parent_id][acc_key] += groups_data[group_id][acc_key]
                if foreign_currency:
                    groups_data[parent_id]["initial_currency_balance"] += groups_data[
                        group_id
                    ]["initial_currency_balance"]
                    groups_data[parent_id]["ending_currency_balance"] += groups_data[
                        group_id
                    ]["ending_currency_balance"]
                parent_id = groups_data[parent_id]["parent_id"]
        return groups_data

    def _get_groups_data(self, accounts_data, total_amount, foreign_currency):
        accounts_ids = list(accounts_data.keys())
        accounts = (
            self.env["account.account"]
            .with_context(active_test=False)
            .browse(accounts_ids)
        )
        account_group_relation = {}
        for account in accounts:
            accounts_data[account.id]["complete_code"] = (
                account.group_id.complete_code + " / " + account.code
                if account.group_id.id
                else ""
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
                        "code": group.code_prefix_start,
                        "name": group.name,
                        "parent_id": group.parent_id.id,
                        "type": "group_type",
                        "complete_code": group.complete_code,
                        "account_ids": [],
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
        groups_data = self._get_hierarchy_groups(
            group_ids,
            groups_data,
            foreign_currency,
        )
        # Accounts of the report below each group, for the drill-down domains
        for group_id, account_ids in account_group_relation.items():
            while group_id:
                groups_data[group_id]["account_ids"] += account_ids
                group_id = groups_data[group_id]["parent_id"]
        return groups_data

    def _get_aml_domain_common(self, data):
        """Filters of the wizard that every drill-down domain must keep."""
        if data["only_posted_moves"]:
            domain = [("parent_state", "=", "posted")]
        else:
            domain = [("parent_state", "in", ("posted", "draft"))]
        if data["company_id"]:
            domain += [("company_id", "=", data["company_id"])]
        if data["journal_ids"]:
            domain += [("journal_id", "in", data["journal_ids"])]
        if data["partner_ids"]:
            domain += [("partner_id", "in", data["partner_ids"])]
        return domain

    def _get_partner_lines(self, account, total_amount, partners_data):
        """Rows of the partners of a receivable or payable account."""
        lines = []
        acc_amounts = total_amount[account["id"]]
        for partner_id, amounts in acc_amounts.items():
            if not isinstance(partner_id, int):
                continue
            line = dict(
                amounts,
                type="partner_type",
                id=partner_id,
                account_id=account["id"],
                code="",
                name=partners_data[partner_id]["name"],
                currency_id=account["currency_id"],
                currency_name=account["currency_name"],
                aml_domain=[
                    ("account_id", "=", account["id"]),
                    ("partner_id", "=", partner_id or False),
                ],
                pl_domain=account["pl_domain"],
            )
            if "level" in account:
                line["level"] = account["level"] + 1
            lines.append(line)
        return lines

    def _get_report_values(self, docids, data):
        res = super()._get_report_values(docids, data)
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
        show_hierarchy = data["show_hierarchy"]
        show_hierarchy_level = data["show_hierarchy_level"]
        foreign_currency = data["foreign_currency"]
        only_posted_moves = data["only_posted_moves"]
        unaffected_earnings_account = data["unaffected_earnings_account"]
        fy_start_date = data["fy_start_date"]
        grouped_by = data["grouped_by"]
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
            grouped_by,
        )
        amount_keys = [
            "initial_balance",
            "debit",
            "credit",
            "balance",
            "ending_balance",
        ]
        # The initial balance of profit and loss accounts starts with the
        # fiscal year: the drill-down domains must do the same.
        pl_domain = [
            ("date", ">=", fields.Date.to_string(fields.Date.to_date(fy_start_date)))
        ]
        for account_id, account_data in accounts_data.items():
            account_amounts = total_amount[account_id]
            account_data.update({key: account_amounts[key] for key in amount_keys})
            account_data.update(
                {
                    "group_by": account_amounts.get("group_by", False),
                    "group_by_data": account_amounts.get("group_by_data", False),
                    "type": "account_type",
                    "has_partners": any(
                        isinstance(key, int) for key in account_amounts
                    ),
                    "aml_domain": [("account_id", "=", account_id)],
                    "pl_domain": (
                        [] if account_data["include_initial_balance"] else pl_domain
                    ),
                }
            )
            if foreign_currency:
                account_data.update(
                    {
                        "ending_currency_balance": account_amounts[
                            "ending_currency_balance"
                        ],
                        "initial_currency_balance": account_amounts[
                            "initial_currency_balance"
                        ],
                    }
                )
                account_amounts["currency_id"] = account_data["currency_id"]
                account_amounts["currency_name"] = account_data["currency_name"]
        trial_balance_grouped = False
        total_amount_grouped = False
        if grouped_by:
            trial_balance_grouped, total_amount_grouped = self._get_data_grouped(
                total_amount, accounts_data, foreign_currency
            )
        if show_hierarchy:
            groups_data = self._get_groups_data(
                accounts_data, total_amount, foreign_currency
            )
            for group_data in groups_data.values():
                group_data.update(
                    aml_domain=[("account_id", "in", group_data["account_ids"])],
                    pl_domain=[],
                )
            trial_balance = list(groups_data.values())
            trial_balance += list(accounts_data.values())
            trial_balance = sorted(trial_balance, key=lambda k: k["complete_code"])
            for trial in trial_balance:
                counter = trial["complete_code"].count("/")
                trial["level"] = counter
        else:
            trial_balance = sorted(accounts_data.values(), key=lambda k: k["code"])
        if show_partner_details:
            lines = []
            for line in trial_balance:
                lines.append(line)
                if line["type"] == "account_type" and line["has_partners"]:
                    lines += self._get_partner_lines(line, total_amount, partners_data)
            trial_balance = lines
        total_line = {
            "type": "total",
            "name": _("Total"),
            "code": "",
            "currency_id": False,
            "currency_name": False,
            "initial_currency_balance": 0.0,
            "ending_currency_balance": 0.0,
        }
        for key in amount_keys:
            total_line[key] = sum(
                account_data[key] for account_data in accounts_data.values()
            )
        res.update(
            {
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
                "show_hierarchy": show_hierarchy,
                "hide_parent_hierarchy_level": data["hide_parent_hierarchy_level"],
                "trial_balance": trial_balance,
                "trial_balance_grouped": trial_balance_grouped,
                "total_line": total_line,
                "total_amount": total_amount,
                "total_amount_grouped": total_amount_grouped,
                "accounts_data": accounts_data,
                "partners_data": partners_data,
                "show_hierarchy_level": show_hierarchy_level,
                "currency_model": self.env["res.currency"],
                "grouped_by": grouped_by,
                "aml_domain_common": self._get_aml_domain_common(data),
            }
        )
        return res
