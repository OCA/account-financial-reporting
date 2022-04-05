# © 2016 Julien Coux (Camptocamp)
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import calendar
import datetime
import operator

from odoo import _, api, models
from odoo.tools import float_is_zero


class GeneralLedgerReport(models.AbstractModel):
    _name = "report.account_financial_report.general_ledger"
    _description = "General Ledger Report"
    _inherit = "report.account_financial_report.abstract_report"

    def _get_tags_data(self, tags_ids):
        tags = self.env["account.analytic.tag"].browse(tags_ids)
        tags_data = {}
        for tag in tags:
            tags_data.update({tag.id: {"name": tag.name}})
        return tags_data

    def _get_taxes_data(self, taxes_ids):
        taxes = self.env["account.tax"].browse(taxes_ids)
        taxes_data = {}
        for tax in taxes:
            taxes_data.update(
                {
                    tax.id: {
                        "id": tax.id,
                        "amount": tax.amount,
                        "amount_type": tax.amount_type,
                        "display_name": tax.display_name,
                    }
                }
            )
            if tax.amount_type == "percent" or tax.amount_type == "division":
                taxes_data[tax.id]["string"] = "%"
            else:
                taxes_data[tax.id]["string"] = ""
            taxes_data[tax.id]["tax_name"] = (
                tax.display_name
                + " ("
                + str(tax.amount)
                + taxes_data[tax.id]["string"]
                + ")"
            )
        return taxes_data

    def _get_acc_prt_accounts_ids(self, company_id):
        accounts_domain = [
            ("company_id", "=", company_id),
            ("internal_type", "in", ["receivable", "payable"]),
        ]
        acc_prt_accounts = self.env["account.account"].search(accounts_domain)
        return acc_prt_accounts.ids

    def _get_initial_balances_bs_ml_domain(
        self, account_ids, company_id, date_from, base_domain, acc_prt=False
    ):
        accounts_domain = [
            ("company_id", "=", company_id),
            ("user_type_id.include_initial_balance", "=", True),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = []
        domain += base_domain
        domain += [("date", "<", date_from)]
        accounts = self.env["account.account"].search(accounts_domain)
        domain += [("account_id", "in", accounts.ids)]
        if acc_prt:
            domain += [("account_id.internal_type", "in", ["receivable", "payable"])]
        return domain

    def _get_initial_balances_pl_ml_domain(
        self, account_ids, company_id, date_from, fy_start_date, base_domain
    ):
        accounts_domain = [
            ("company_id", "=", company_id),
            ("user_type_id.include_initial_balance", "=", False),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = []
        domain += base_domain
        domain += [("date", "<", date_from), ("date", ">=", fy_start_date)]
        accounts = self.env["account.account"].search(accounts_domain)
        domain += [("account_id", "in", accounts.ids)]
        return domain

    def _get_accounts_initial_balance(self, initial_domain_bs, initial_domain_pl):
        gl_initial_acc_bs = self.env["account.move.line"].read_group(
            domain=initial_domain_bs,
            fields=["account_id", "debit", "credit", "balance", "amount_currency"],
            groupby=["account_id"],
        )
        gl_initial_acc_pl = self.env["account.move.line"].read_group(
            domain=initial_domain_pl,
            fields=["account_id", "debit", "credit", "balance", "amount_currency"],
            groupby=["account_id"],
        )
        gl_initial_acc = gl_initial_acc_bs + gl_initial_acc_pl
        return gl_initial_acc

    def _get_initial_balance_fy_pl_ml_domain(
        self, account_ids, company_id, fy_start_date, base_domain
    ):
        accounts_domain = [
            ("company_id", "=", company_id),
            ("user_type_id.include_initial_balance", "=", False),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = []
        domain += base_domain
        domain += [("date", "<", fy_start_date)]
        accounts = self.env["account.account"].search(accounts_domain)
        domain += [("account_id", "in", accounts.ids)]
        return domain

    def _get_pl_initial_balance(
        self, account_ids, company_id, fy_start_date, foreign_currency, base_domain
    ):
        domain = self._get_initial_balance_fy_pl_ml_domain(
            account_ids, company_id, fy_start_date, base_domain
        )
        initial_balances = self.env["account.move.line"].read_group(
            domain=domain,
            fields=["account_id", "debit", "credit", "balance", "amount_currency"],
            groupby=["account_id"],
        )
        pl_initial_balance = {
            "debit": 0.0,
            "credit": 0.0,
            "balance": 0.0,
            "bal_curr": 0.0,
        }
        for initial_balance in initial_balances:
            pl_initial_balance["debit"] += initial_balance["debit"]
            pl_initial_balance["credit"] += initial_balance["credit"]
            pl_initial_balance["balance"] += initial_balance["balance"]
            pl_initial_balance["bal_curr"] += initial_balance["amount_currency"]
        return pl_initial_balance

    def _get_initial_balance_data(
        self,
        account_ids,
        partner_ids,
        company_id,
        date_from,
        foreign_currency,
        only_posted_moves,
        unaffected_earnings_account,
        fy_start_date,
        analytic_tag_ids,
        cost_center_ids,
        extra_domain,
    ):
        # If explicit list of accounts is provided,
        # don't include unaffected earnings account
        if account_ids:
            unaffected_earnings_account = False
        base_domain = []
        if company_id:
            base_domain += [("company_id", "=", company_id)]
        if partner_ids:
            base_domain += [("partner_id", "in", partner_ids)]
        if only_posted_moves:
            base_domain += [("move_id.state", "=", "posted")]
        else:
            base_domain += [("move_id.state", "in", ["posted", "draft"])]
        if analytic_tag_ids:
            base_domain += [("analytic_tag_ids", "in", analytic_tag_ids)]
        if cost_center_ids:
            base_domain += [("analytic_account_id", "in", cost_center_ids)]
        if extra_domain:
            base_domain += extra_domain
        initial_domain_bs = self._get_initial_balances_bs_ml_domain(
            account_ids, company_id, date_from, base_domain
        )
        initial_domain_pl = self._get_initial_balances_pl_ml_domain(
            account_ids, company_id, date_from, fy_start_date, base_domain
        )
        gl_initial_acc = self._get_accounts_initial_balance(
            initial_domain_bs, initial_domain_pl
        )
        initial_domain_acc_prt = self._get_initial_balances_bs_ml_domain(
            account_ids, company_id, date_from, base_domain, acc_prt=True
        )
        gl_initial_acc_prt = self.env["account.move.line"].read_group(
            domain=initial_domain_acc_prt,
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
        gen_ld_data = {}
        for gl in gl_initial_acc:
            acc_id = gl["account_id"][0]
            gen_ld_data[acc_id] = {}
            gen_ld_data[acc_id]["id"] = acc_id
            gen_ld_data[acc_id]["partners"] = False
            gen_ld_data[acc_id]["init_bal"] = {}
            gen_ld_data[acc_id]["init_bal"]["credit"] = gl["credit"]
            gen_ld_data[acc_id]["init_bal"]["debit"] = gl["debit"]
            gen_ld_data[acc_id]["init_bal"]["balance"] = gl["balance"]
            gen_ld_data[acc_id]["fin_bal"] = {}
            gen_ld_data[acc_id]["fin_bal"]["credit"] = gl["credit"]
            gen_ld_data[acc_id]["fin_bal"]["debit"] = gl["debit"]
            gen_ld_data[acc_id]["fin_bal"]["balance"] = gl["balance"]
            gen_ld_data[acc_id]["init_bal"]["bal_curr"] = gl["amount_currency"]
            gen_ld_data[acc_id]["fin_bal"]["bal_curr"] = gl["amount_currency"]
        partners_data = {}
        partners_ids = set()
        if gl_initial_acc_prt:
            for gl in gl_initial_acc_prt:
                if not gl["partner_id"]:
                    prt_id = 0
                    prt_name = "Missing Partner"
                else:
                    prt_id = gl["partner_id"][0]
                    prt_name = gl["partner_id"][1]
                    prt_name = prt_name._value
                if prt_id not in partners_ids:
                    partners_ids.add(prt_id)
                    partners_data.update({prt_id: {"id": prt_id, "name": prt_name}})
                acc_id = gl["account_id"][0]
                gen_ld_data[acc_id][prt_id] = {}
                gen_ld_data[acc_id][prt_id]["id"] = prt_id
                gen_ld_data[acc_id]["partners"] = True
                gen_ld_data[acc_id][prt_id]["init_bal"] = {}
                gen_ld_data[acc_id][prt_id]["init_bal"]["credit"] = gl["credit"]
                gen_ld_data[acc_id][prt_id]["init_bal"]["debit"] = gl["debit"]
                gen_ld_data[acc_id][prt_id]["init_bal"]["balance"] = gl["balance"]
                gen_ld_data[acc_id][prt_id]["fin_bal"] = {}
                gen_ld_data[acc_id][prt_id]["fin_bal"]["credit"] = gl["credit"]
                gen_ld_data[acc_id][prt_id]["fin_bal"]["debit"] = gl["debit"]
                gen_ld_data[acc_id][prt_id]["fin_bal"]["balance"] = gl["balance"]
                gen_ld_data[acc_id][prt_id]["init_bal"]["bal_curr"] = gl[
                    "amount_currency"
                ]
                gen_ld_data[acc_id][prt_id]["fin_bal"]["bal_curr"] = gl[
                    "amount_currency"
                ]
        accounts_ids = list(gen_ld_data.keys())
        unaffected_id = unaffected_earnings_account
        if unaffected_id:
            if unaffected_id not in accounts_ids:
                accounts_ids.append(unaffected_id)
                self._initialize_account(gen_ld_data, unaffected_id, foreign_currency)
            pl_initial_balance = self._get_pl_initial_balance(
                account_ids, company_id, fy_start_date, foreign_currency, base_domain
            )
            gen_ld_data[unaffected_id]["init_bal"]["debit"] += pl_initial_balance[
                "debit"
            ]
            gen_ld_data[unaffected_id]["init_bal"]["credit"] += pl_initial_balance[
                "credit"
            ]
            gen_ld_data[unaffected_id]["init_bal"]["balance"] += pl_initial_balance[
                "balance"
            ]
            gen_ld_data[unaffected_id]["fin_bal"]["debit"] += pl_initial_balance[
                "debit"
            ]
            gen_ld_data[unaffected_id]["fin_bal"]["credit"] += pl_initial_balance[
                "credit"
            ]
            gen_ld_data[unaffected_id]["fin_bal"]["balance"] += pl_initial_balance[
                "balance"
            ]
            if foreign_currency:
                gen_ld_data[unaffected_id]["init_bal"][
                    "bal_curr"
                ] += pl_initial_balance["bal_curr"]
                gen_ld_data[unaffected_id]["fin_bal"]["bal_curr"] += pl_initial_balance[
                    "bal_curr"
                ]
        return gen_ld_data, partners_data, partner_ids

    @api.model
    def _get_move_line_data(self, move_line):
        move_line_data = {
            "id": move_line["id"],
            "date": move_line["date"],
            "entry": move_line["move_id"][1],
            "entry_id": move_line["move_id"][0],
            "journal_id": move_line["journal_id"][0],
            "account_id": move_line["account_id"][0],
            "partner_id": move_line["partner_id"][0]
            if move_line["partner_id"]
            else False,
            "partner_name": move_line["partner_id"][1]
            if move_line["partner_id"]
            else "",
            "ref": "" if not move_line["ref"] else move_line["ref"],
            "name": "" if not move_line["name"] else move_line["name"],
            "tax_ids": move_line["tax_ids"],
            "debit": move_line["debit"],
            "credit": move_line["credit"],
            "balance": move_line["balance"],
            "bal_curr": move_line["amount_currency"],
            "rec_id": move_line["full_reconcile_id"][0]
            if move_line["full_reconcile_id"]
            else False,
            "rec_name": move_line["full_reconcile_id"][1]
            if move_line["full_reconcile_id"]
            else "",
            "tag_ids": move_line["analytic_tag_ids"],
            "currency_id": move_line["currency_id"],
            "analytic_account": move_line["analytic_account_id"][1]
            if move_line["analytic_account_id"]
            else "",
            "analytic_account_id": move_line["analytic_account_id"][0]
            if move_line["analytic_account_id"]
            else False,
        }
        if (
            move_line_data["ref"] == move_line_data["name"]
            or move_line_data["ref"] == ""
        ):
            ref_label = move_line_data["name"]
        elif move_line_data["name"] == "":
            ref_label = move_line_data["ref"]
        else:
            ref_label = move_line_data["ref"] + str(" - ") + move_line_data["name"]
        move_line_data.update({"ref_label": ref_label})
        return move_line_data

    @api.model
    def _get_period_domain(
        self,
        account_ids,
        partner_ids,
        company_id,
        only_posted_moves,
        date_to,
        date_from,
        analytic_tag_ids,
        cost_center_ids,
    ):
        domain = [
            ("display_type", "=", False),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
        ]
        if account_ids:
            domain += [("account_id", "in", account_ids)]
        if company_id:
            domain += [("company_id", "=", company_id)]
        if partner_ids:
            domain += [("partner_id", "in", partner_ids)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        else:
            domain += [("move_id.state", "in", ["posted", "draft"])]
        if analytic_tag_ids:
            domain += [("analytic_tag_ids", "in", analytic_tag_ids)]
        if cost_center_ids:
            domain += [("analytic_account_id", "in", cost_center_ids)]
        return domain

    @api.model
    def _initialize_partner(self, gen_ld_data, acc_id, prt_id, foreign_currency):
        gen_ld_data[acc_id]["partners"] = True
        gen_ld_data[acc_id][prt_id] = {}
        gen_ld_data[acc_id][prt_id]["id"] = prt_id
        gen_ld_data[acc_id][prt_id]["init_bal"] = {}
        gen_ld_data[acc_id][prt_id]["init_bal"]["balance"] = 0.0
        gen_ld_data[acc_id][prt_id]["init_bal"]["credit"] = 0.0
        gen_ld_data[acc_id][prt_id]["init_bal"]["debit"] = 0.0
        gen_ld_data[acc_id][prt_id]["fin_bal"] = {}
        gen_ld_data[acc_id][prt_id]["fin_bal"]["credit"] = 0.0
        gen_ld_data[acc_id][prt_id]["fin_bal"]["debit"] = 0.0
        gen_ld_data[acc_id][prt_id]["fin_bal"]["balance"] = 0.0
        if foreign_currency:
            gen_ld_data[acc_id][prt_id]["init_bal"]["bal_curr"] = 0.0
            gen_ld_data[acc_id][prt_id]["fin_bal"]["bal_curr"] = 0.0
        return gen_ld_data

    def _initialize_account(self, gen_ld_data, acc_id, foreign_currency):
        gen_ld_data[acc_id] = {}
        gen_ld_data[acc_id]["id"] = acc_id
        gen_ld_data[acc_id]["partners"] = False
        gen_ld_data[acc_id]["init_bal"] = {}
        gen_ld_data[acc_id]["init_bal"]["balance"] = 0.0
        gen_ld_data[acc_id]["init_bal"]["credit"] = 0.0
        gen_ld_data[acc_id]["init_bal"]["debit"] = 0.0
        gen_ld_data[acc_id]["fin_bal"] = {}
        gen_ld_data[acc_id]["fin_bal"]["credit"] = 0.0
        gen_ld_data[acc_id]["fin_bal"]["debit"] = 0.0
        gen_ld_data[acc_id]["fin_bal"]["balance"] = 0.0
        if foreign_currency:
            gen_ld_data[acc_id]["init_bal"]["bal_curr"] = 0.0
            gen_ld_data[acc_id]["fin_bal"]["bal_curr"] = 0.0
        return gen_ld_data

    def _get_reconciled_after_date_to_ids(self, full_reconcile_ids, date_to):
        full_reconcile_ids = list(full_reconcile_ids)
        domain = [
            ("max_date", ">", date_to),
            ("full_reconcile_id", "in", full_reconcile_ids),
        ]
        fields = ["full_reconcile_id"]
        reconciled_after_date_to = self.env["account.partial.reconcile"].search_read(
            domain=domain, fields=fields
        )
        rec_after_date_to_ids = list(
            map(operator.itemgetter("full_reconcile_id"), reconciled_after_date_to)
        )
        rec_after_date_to_ids = [i[0] for i in rec_after_date_to_ids]
        return rec_after_date_to_ids

    def _get_period_ml_data(
        self,
        account_ids,
        partner_ids,
        company_id,
        foreign_currency,
        only_posted_moves,
        date_from,
        date_to,
        partners_data,
        gen_ld_data,
        partners_ids,
        analytic_tag_ids,
        cost_center_ids,
        extra_domain,
    ):
        domain = self._get_period_domain(
            account_ids,
            partner_ids,
            company_id,
            only_posted_moves,
            date_to,
            date_from,
            analytic_tag_ids,
            cost_center_ids,
        )
        if extra_domain:
            domain += extra_domain
        ml_fields = [
            "id",
            "name",
            "date",
            "move_id",
            "journal_id",
            "account_id",
            "partner_id",
            "debit",
            "credit",
            "balance",
            "currency_id",
            "full_reconcile_id",
            "tax_ids",
            "analytic_tag_ids",
            "amount_currency",
            "ref",
            "name",
            "analytic_account_id",
        ]
        move_lines = self.env["account.move.line"].search_read(
            domain=domain, fields=ml_fields
        )
        journal_ids = set()
        full_reconcile_ids = set()
        taxes_ids = set()
        tags_ids = set()
        full_reconcile_data = {}
        acc_prt_account_ids = self._get_acc_prt_accounts_ids(company_id)
        for move_line in move_lines:
            journal_ids.add(move_line["journal_id"][0])
            for tax_id in move_line["tax_ids"]:
                taxes_ids.add(tax_id)
            for analytic_tag_id in move_line["analytic_tag_ids"]:
                tags_ids.add(analytic_tag_id)
            if move_line["full_reconcile_id"]:
                rec_id = move_line["full_reconcile_id"][0]
                if rec_id not in full_reconcile_ids:
                    full_reconcile_data.update(
                        {
                            rec_id: {
                                "id": rec_id,
                                "name": move_line["full_reconcile_id"][1],
                            }
                        }
                    )
                    full_reconcile_ids.add(rec_id)
            acc_id = move_line["account_id"][0]
            ml_id = move_line["id"]
            if move_line["partner_id"]:
                prt_id = move_line["partner_id"][0]
                partner_name = move_line["partner_id"][1]
            if acc_id not in gen_ld_data.keys():
                gen_ld_data = self._initialize_account(
                    gen_ld_data, acc_id, foreign_currency
                )
            if acc_id in acc_prt_account_ids:
                if not move_line["partner_id"]:
                    prt_id = 0
                    partner_name = "Missing Partner"
                partners_ids.append(prt_id)
                partners_data.update({prt_id: {"id": prt_id, "name": partner_name}})
                if prt_id not in gen_ld_data[acc_id]:
                    gen_ld_data = self._initialize_partner(
                        gen_ld_data, acc_id, prt_id, foreign_currency
                    )
                gen_ld_data[acc_id][prt_id][ml_id] = self._get_move_line_data(move_line)
                gen_ld_data[acc_id][prt_id]["fin_bal"]["credit"] += move_line["credit"]
                gen_ld_data[acc_id][prt_id]["fin_bal"]["debit"] += move_line["debit"]
                gen_ld_data[acc_id][prt_id]["fin_bal"]["balance"] += move_line[
                    "balance"
                ]
                if foreign_currency:
                    gen_ld_data[acc_id][prt_id]["fin_bal"]["bal_curr"] += move_line[
                        "amount_currency"
                    ]
            else:
                gen_ld_data[acc_id][ml_id] = self._get_move_line_data(move_line)
            gen_ld_data[acc_id]["fin_bal"]["credit"] += move_line["credit"]
            gen_ld_data[acc_id]["fin_bal"]["debit"] += move_line["debit"]
            gen_ld_data[acc_id]["fin_bal"]["balance"] += move_line["balance"]
            if foreign_currency:
                gen_ld_data[acc_id]["fin_bal"]["bal_curr"] += move_line[
                    "amount_currency"
                ]
        journals_data = self._get_journals_data(list(journal_ids))
        accounts_data = self._get_accounts_data(gen_ld_data.keys())
        taxes_data = self._get_taxes_data(list(taxes_ids))
        tags_data = self._get_tags_data(list(tags_ids))
        rec_after_date_to_ids = self._get_reconciled_after_date_to_ids(
            full_reconcile_data.keys(), date_to
        )
        return (
            gen_ld_data,
            accounts_data,
            partners_data,
            journals_data,
            full_reconcile_data,
            taxes_data,
            tags_data,
            rec_after_date_to_ids,
        )

    @api.model
    def _recalculate_cumul_balance(
        self, move_lines, last_cumul_balance, rec_after_date_to_ids
    ):
        for move_line in move_lines:
            move_line["balance"] += last_cumul_balance
            last_cumul_balance = move_line["balance"]
            if move_line["rec_id"] in rec_after_date_to_ids:
                move_line["rec_name"] = "(" + _("future") + ") " + move_line["rec_name"]
        return move_lines

    def _create_account(self, account, acc_id, gen_led_data, rec_after_date_to_ids):
        move_lines = []
        for ml_id in gen_led_data[acc_id].keys():
            if not isinstance(ml_id, int):
                account.update({ml_id: gen_led_data[acc_id][ml_id]})
            else:
                move_lines += [gen_led_data[acc_id][ml_id]]
        move_lines = sorted(move_lines, key=lambda k: (k["date"]))
        move_lines = self._recalculate_cumul_balance(
            move_lines,
            gen_led_data[acc_id]["init_bal"]["balance"],
            rec_after_date_to_ids,
        )
        account.update({"move_lines": move_lines})
        return account

    def _create_account_not_show_partner(
        self, account, acc_id, gen_led_data, rec_after_date_to_ids
    ):
        move_lines = []
        for prt_id in gen_led_data[acc_id].keys():
            if not isinstance(prt_id, int):
                account.update({prt_id: gen_led_data[acc_id][prt_id]})
            else:
                for ml_id in gen_led_data[acc_id][prt_id].keys():
                    if isinstance(ml_id, int):
                        move_lines += [gen_led_data[acc_id][prt_id][ml_id]]
        move_lines = sorted(move_lines, key=lambda k: (k["date"]))
        move_lines = self._recalculate_cumul_balance(
            move_lines,
            gen_led_data[acc_id]["init_bal"]["balance"],
            rec_after_date_to_ids,
        )
        account.update({"move_lines": move_lines, "partners": False})
        return account

    def _create_general_ledger(
        self,
        gen_led_data,
        accounts_data,
        show_partner_details,
        rec_after_date_to_ids,
        hide_account_at_0,
    ):
        general_ledger = []
        rounding = self.env.company.currency_id.rounding
        for acc_id in gen_led_data.keys():
            account = {}
            account.update(
                {
                    "code": accounts_data[acc_id]["code"],
                    "name": accounts_data[acc_id]["name"],
                    "type": "account",
                    "currency_id": accounts_data[acc_id]["currency_id"],
                    "centralized": accounts_data[acc_id]["centralized"],
                }
            )
            if not gen_led_data[acc_id]["partners"]:
                account = self._create_account(
                    account, acc_id, gen_led_data, rec_after_date_to_ids
                )
                if (
                    hide_account_at_0
                    and float_is_zero(
                        gen_led_data[acc_id]["init_bal"]["balance"],
                        precision_rounding=rounding,
                    )
                    and account["move_lines"] == []
                ):
                    continue
            else:
                if show_partner_details:
                    list_partner = []
                    for prt_id in gen_led_data[acc_id].keys():
                        partner = {}
                        move_lines = []
                        if not isinstance(prt_id, int):
                            account.update({prt_id: gen_led_data[acc_id][prt_id]})
                        else:
                            for ml_id in gen_led_data[acc_id][prt_id].keys():
                                if not isinstance(ml_id, int):
                                    partner.update(
                                        {ml_id: gen_led_data[acc_id][prt_id][ml_id]}
                                    )
                                else:
                                    move_lines += [gen_led_data[acc_id][prt_id][ml_id]]
                            move_lines = sorted(move_lines, key=lambda k: (k["date"]))
                            move_lines = self._recalculate_cumul_balance(
                                move_lines,
                                gen_led_data[acc_id][prt_id]["init_bal"]["balance"],
                                rec_after_date_to_ids,
                            )
                            partner.update({"move_lines": move_lines})
                            if (
                                hide_account_at_0
                                and float_is_zero(
                                    gen_led_data[acc_id][prt_id]["init_bal"]["balance"],
                                    precision_rounding=rounding,
                                )
                                and partner["move_lines"] == []
                            ):
                                continue
                            list_partner += [partner]
                    account.update({"list_partner": list_partner})
                    if (
                        hide_account_at_0
                        and float_is_zero(
                            gen_led_data[acc_id]["init_bal"]["balance"],
                            precision_rounding=rounding,
                        )
                        and account["list_partner"] == []
                    ):
                        continue
                else:
                    account = self._create_account_not_show_partner(
                        account, acc_id, gen_led_data, rec_after_date_to_ids
                    )
                    if (
                        hide_account_at_0
                        and float_is_zero(
                            gen_led_data[acc_id]["init_bal"]["balance"],
                            precision_rounding=rounding,
                        )
                        and account["move_lines"] == []
                    ):
                        continue
            general_ledger += [account]
        return general_ledger

    @api.model
    def _calculate_centralization(self, centralized_ml, move_line, date_to):
        jnl_id = move_line["journal_id"]
        month = move_line["date"].month
        if jnl_id not in centralized_ml.keys():
            centralized_ml[jnl_id] = {}
        if month not in centralized_ml[jnl_id].keys():
            centralized_ml[jnl_id][month] = {}
            last_day_month = calendar.monthrange(move_line["date"].year, month)
            date = datetime.date(move_line["date"].year, month, last_day_month[1])
            if date > date_to:
                date = date_to
            centralized_ml[jnl_id][month].update(
                {
                    "journal_id": jnl_id,
                    "ref_label": "Centralized entries",
                    "date": date,
                    "debit": 0.0,
                    "credit": 0.0,
                    "balance": 0.0,
                    "bal_curr": 0.0,
                    "partner_id": False,
                    "rec_id": 0,
                    "entry_id": False,
                    "tax_ids": [],
                    "full_reconcile_id": False,
                    "id": False,
                    "tag_ids": False,
                    "currency_id": False,
                    "analytic_account_id": False,
                }
            )
        centralized_ml[jnl_id][month]["debit"] += move_line["debit"]
        centralized_ml[jnl_id][month]["credit"] += move_line["credit"]
        centralized_ml[jnl_id][month]["balance"] += (
            move_line["debit"] - move_line["credit"]
        )
        centralized_ml[jnl_id][month]["bal_curr"] += move_line["bal_curr"]
        return centralized_ml

    @api.model
    def _get_centralized_ml(self, account, date_to):
        centralized_ml = {}
        if isinstance(date_to, str):
            date_to = datetime.datetime.strptime(date_to, "%Y-%m-%d").date()
        if account["partners"]:
            for partner in account["list_partner"]:
                for move_line in partner["move_lines"]:
                    centralized_ml = self._calculate_centralization(
                        centralized_ml,
                        move_line,
                        date_to,
                    )
        else:
            for move_line in account["move_lines"]:
                centralized_ml = self._calculate_centralization(
                    centralized_ml,
                    move_line,
                    date_to,
                )
        list_centralized_ml = []
        for jnl_id in centralized_ml.keys():
            list_centralized_ml += list(centralized_ml[jnl_id].values())
        return list_centralized_ml

    def _get_report_values(self, docids, data):
        wizard_id = data["wizard_id"]
        company = self.env["res.company"].browse(data["company_id"])
        company_id = data["company_id"]
        date_to = data["date_to"]
        date_from = data["date_from"]
        partner_ids = data["partner_ids"]
        if not partner_ids:
            filter_partner_ids = False
        else:
            filter_partner_ids = True
        account_ids = data["account_ids"]
        analytic_tag_ids = data["analytic_tag_ids"]
        cost_center_ids = data["cost_center_ids"]
        show_partner_details = data["show_partner_details"]
        hide_account_at_0 = data["hide_account_at_0"]
        foreign_currency = data["foreign_currency"]
        only_posted_moves = data["only_posted_moves"]
        unaffected_earnings_account = data["unaffected_earnings_account"]
        fy_start_date = data["fy_start_date"]
        extra_domain = data["domain"]
        gen_ld_data, partners_data, partners_ids = self._get_initial_balance_data(
            account_ids,
            partner_ids,
            company_id,
            date_from,
            foreign_currency,
            only_posted_moves,
            unaffected_earnings_account,
            fy_start_date,
            analytic_tag_ids,
            cost_center_ids,
            extra_domain,
        )
        centralize = data["centralize"]
        (
            gen_ld_data,
            accounts_data,
            partners_data,
            journals_data,
            full_reconcile_data,
            taxes_data,
            tags_data,
            rec_after_date_to_ids,
        ) = self._get_period_ml_data(
            account_ids,
            partner_ids,
            company_id,
            foreign_currency,
            only_posted_moves,
            date_from,
            date_to,
            partners_data,
            gen_ld_data,
            partners_ids,
            analytic_tag_ids,
            cost_center_ids,
            extra_domain,
        )
        general_ledger = self._create_general_ledger(
            gen_ld_data,
            accounts_data,
            show_partner_details,
            rec_after_date_to_ids,
            hide_account_at_0,
        )
        if centralize:
            for account in general_ledger:
                if account["centralized"]:
                    centralized_ml = self._get_centralized_ml(account, date_to)
                    account["move_lines"] = centralized_ml
                    account["move_lines"] = self._recalculate_cumul_balance(
                        account["move_lines"],
                        gen_ld_data[account["id"]]["init_bal"]["balance"],
                        rec_after_date_to_ids,
                    )
                    if account["partners"]:
                        account["partners"] = False
                        del account["list_partner"]
        general_ledger = sorted(general_ledger, key=lambda k: k["code"])
        return {
            "doc_ids": [wizard_id],
            "doc_model": "general.ledger.report.wizard",
            "docs": self.env["general.ledger.report.wizard"].browse(wizard_id),
            "foreign_currency": data["foreign_currency"],
            "company_name": company.display_name,
            "company_currency": company.currency_id,
            "currency_name": company.currency_id.name,
            "date_from": data["date_from"],
            "date_to": data["date_to"],
            "only_posted_moves": data["only_posted_moves"],
            "hide_account_at_0": data["hide_account_at_0"],
            "show_analytic_tags": data["show_analytic_tags"],
            "show_cost_center": data["show_cost_center"],
            "general_ledger": general_ledger,
            "accounts_data": accounts_data,
            "partners_data": partners_data,
            "journals_data": journals_data,
            "full_reconcile_data": full_reconcile_data,
            "taxes_data": taxes_data,
            "centralize": centralize,
            "tags_data": tags_data,
            "filter_partner_ids": filter_partner_ids,
        }
