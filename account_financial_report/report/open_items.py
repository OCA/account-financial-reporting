# © 2016 Julien Coux (Camptocamp)
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import operator
from datetime import date, datetime

from odoo import api, models
from odoo.osv import expression
from odoo.tools import float_is_zero


class OpenItemsReport(models.AbstractModel):
    _name = "report.account_financial_report.open_items"
    _description = "Open Items Report"

    @api.model
    def get_html(self, given_context=None):
        return self._get_html()

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        rcontext.update(context.get("data"))
        active_id = context.get("active_id")
        wiz = self.env["open.items.report.wizard"].browse(active_id)
        rcontext["o"] = wiz
        result["html"] = self.env.ref(
            "account_financial_report.report_open_items"
        ).render(rcontext)
        return result

    def _get_account_partial_reconciled(self, move_lines_data, date_at_object):
        reconciled_ids = []
        for move_line in move_lines_data:
            if move_line["reconciled"]:
                reconciled_ids += [move_line["id"]]
        domain = [("max_date", ">=", date_at_object)]
        domain += expression.OR(
            [
                [("debit_move_id", "in", reconciled_ids)],
                [("credit_move_id", "in", reconciled_ids)],
            ]
        )
        fields = ["debit_move_id", "credit_move_id", "amount"]
        accounts_partial_reconcile = self.env["account.partial.reconcile"].search_read(
            domain=domain, fields=fields
        )
        debit_accounts_partial_amount = {}
        credit_accounts_partial_amount = {}
        for account_partial_reconcile_data in accounts_partial_reconcile:
            debit_move_id = account_partial_reconcile_data["debit_move_id"][0]
            credit_move_id = account_partial_reconcile_data["credit_move_id"][0]
            if debit_move_id not in debit_accounts_partial_amount.keys():
                debit_accounts_partial_amount[debit_move_id] = 0.0
            debit_accounts_partial_amount[
                debit_move_id
            ] += account_partial_reconcile_data["amount"]
            if credit_move_id not in credit_accounts_partial_amount.keys():
                credit_accounts_partial_amount[credit_move_id] = 0.0
            credit_accounts_partial_amount[
                credit_move_id
            ] += account_partial_reconcile_data["amount"]
            account_partial_reconcile_data.update(
                {"debit_move_id": debit_move_id, "credit_move_id": credit_move_id}
            )
        return (
            accounts_partial_reconcile,
            debit_accounts_partial_amount,
            credit_accounts_partial_amount,
        )

    @api.model
    def _get_query_domain(
        self,
        account_ids,
        partner_ids,
        date_at_object,
        target_move,
        company_id,
        date_from,
    ):
        query = """
            WHERE aml.account_id in %s and aml.company_id = %s
        """ % (
            tuple(account_ids) if len(account_ids) > 1 else "(%s)" % account_ids[0],
            company_id,
        )
        if date_from:
            query += " and aml.date >= '%s'" % date_from
        if partner_ids:
            query += " and aml.partner_id in {}".format(tuple(partner_ids))
        if target_move == "posted":
            query += " and am.state = 'posted'"
        if date_at_object >= date.today():
            query += " and aml.reconciled IS FALSE"
        else:
            query += (
                """ and ((aml.reconciled IS FALSE OR aml.date >= '%s')
            OR aml.full_reconcile_id IS NOT NULL)"""
                % date_at_object
            )
        return query

    @api.model
    def _get_query(
        self,
        account_ids,
        partner_ids,
        date_at_object,
        target_move,
        company_id,
        date_from,
    ):
        aml_fields = [
            "id",
            "date",
            "move_id",
            "journal_id",
            "account_id",
            "partner_id",
            "ref",
            "date_maturity",
            "amount_residual",
            "amount_currency",
            "amount_residual_currency",
            "debit",
            "credit",
            "currency_id",
            "reconciled",
            "full_reconcile_id",
        ]
        query = ""

        # SELECT
        for field in aml_fields:
            if not query:
                query = "SELECT aml.%s" % field
            else:
                query += ", aml.%s" % field
        # name from res_partner
        query += ", rp.name as partner_name"
        # name from res_currency
        query += ", rc.name as currency_name"
        # state and name from account_move
        query += ", am.state, am.name as move_name"

        # FROM
        query += """
            FROM account_move_line as aml
            LEFT JOIN res_partner as rp
                ON aml.partner_id = rp.id
            LEFT JOIN res_currency as rc
                ON aml.currency_id = rc.id
            LEFT JOIN account_move as am
                ON am.id = aml.move_id
        """

        # WHERE
        query += self._get_query_domain(
            account_ids, partner_ids, date_at_object, target_move, company_id, date_from
        )
        return query

    def _get_accounts_data(self, accounts_ids):
        accounts = self.env["account.account"].browse(accounts_ids)
        accounts_data = {}
        for account in accounts:
            accounts_data.update(
                {
                    account.id: {
                        "id": account.id,
                        "code": account.code,
                        "name": account.name,
                        "hide_account": False,
                        "currency_id": account.currency_id or False,
                        "currency_name": account.currency_id.name,
                    }
                }
            )
        return accounts_data

    def _get_journals_data(self, journals_ids):
        journals = self.env["account.journal"].browse(journals_ids)
        journals_data = {}
        for journal in journals:
            journals_data.update({journal.id: {"id": journal.id, "code": journal.code}})
        return journals_data

    # flake8: noqa: C901
    def _get_data(
        self,
        account_ids,
        partner_ids,
        date_at_object,
        target_move,
        company_id,
        date_from,
    ):
        query = self._get_query(
            account_ids, partner_ids, date_at_object, target_move, company_id, date_from
        )
        self._cr.execute(query)
        move_lines_data = self._cr.dictfetchall()
        account_ids = map(lambda r: r["account_id"], move_lines_data)
        accounts_data = self._get_accounts_data(list(account_ids))
        journal_ids = map(lambda r: r["journal_id"], move_lines_data)
        journals_data = self._get_journals_data(list(journal_ids))

        if date_at_object < date.today():
            (
                accounts_partial_reconcile,
                debit_accounts_partial_amount,
                credit_accounts_partial_amount,
            ) = self._get_account_partial_reconciled(move_lines_data, date_at_object)
            if accounts_partial_reconcile:
                debit_ids = map(
                    operator.itemgetter("debit_move_id"), accounts_partial_reconcile
                )
                credit_ids = map(
                    operator.itemgetter("credit_move_id"), accounts_partial_reconcile
                )
                for move_line in move_lines_data:
                    if move_line["id"] in debit_ids:
                        move_line["amount_residual"] += debit_accounts_partial_amount[
                            move_line["id"]
                        ]
                    if move_line["id"] in credit_ids:
                        move_line["amount_residual"] -= credit_accounts_partial_amount[
                            move_line["id"]
                        ]
            moves_lines_to_remove = []
            for move_line in move_lines_data:
                if move_line["date"] > date_at_object or float_is_zero(
                    move_line["amount_residual"], precision_digits=2
                ):
                    moves_lines_to_remove.append(move_line)
            if len(moves_lines_to_remove) > 0:
                for move_line_to_remove in moves_lines_to_remove:
                    move_lines_data.remove(move_line_to_remove)
        partners_data = {0: {"id": 0, "name": "Missing Partner"}}
        open_items_move_lines_data = {}
        for move_line in move_lines_data:
            no_partner = True
            # Partners data
            if move_line["partner_id"]:
                no_partner = False
                partners_data.update(
                    {
                        move_line["partner_id"]: {
                            "id": move_line["partner_id"],
                            "name": move_line["partner_name"],
                            "currency_id": accounts_data[move_line["account_id"]][
                                "currency_id"
                            ],
                        }
                    }
                )
            else:
                partners_data[0]["currency_id"] = accounts_data[
                    move_line["account_id"]
                ]["currency_id"]

            # Move line update
            original = 0

            if not float_is_zero(move_line["credit"], precision_digits=2):
                original = move_line["credit"] * (-1)
            if not float_is_zero(move_line["debit"], precision_digits=2):
                original = move_line["debit"]
            move_line.update(
                {
                    "date": move_line["date"].strftime("%d/%m/%Y"),
                    "date_maturity": move_line["date_maturity"]
                    and move_line["date_maturity"].strftime("%d/%m/%Y"),
                    "original": original,
                    "partner_id": 0 if no_partner else move_line["partner_id"],
                    "partner_name": "" if no_partner else move_line["partner_name"],
                    "ref": "" if not move_line["ref"] else move_line["ref"],
                    "account": accounts_data[move_line["account_id"]]["code"],
                    "journal": journals_data[move_line["journal_id"]]["code"],
                }
            )

            # Open Items Move Lines Data
            if move_line["account_id"] not in open_items_move_lines_data.keys():
                open_items_move_lines_data[move_line["account_id"]] = {
                    move_line["partner_id"]: [move_line]
                }
            else:
                if (
                    move_line["partner_id"]
                    not in open_items_move_lines_data[move_line["account_id"]].keys()
                ):
                    open_items_move_lines_data[move_line["account_id"]][
                        move_line["partner_id"]
                    ] = [move_line]
                else:
                    open_items_move_lines_data[move_line["account_id"]][
                        move_line["partner_id"]
                    ].append(move_line)
        return (
            move_lines_data,
            partners_data,
            journals_data,
            accounts_data,
            open_items_move_lines_data,
        )

    @api.model
    def _calculate_amounts(self, open_items_move_lines_data):
        total_amount = {}
        for account_id in open_items_move_lines_data.keys():
            total_amount[account_id] = {}
            total_amount[account_id]["residual"] = 0.0
            for partner_id in open_items_move_lines_data[account_id].keys():
                total_amount[account_id][partner_id] = {}
                total_amount[account_id][partner_id]["residual"] = 0.0
                for move_line in open_items_move_lines_data[account_id][partner_id]:
                    total_amount[account_id][partner_id]["residual"] += move_line[
                        "amount_residual"
                    ]
                    total_amount[account_id]["residual"] += move_line["amount_residual"]
        return total_amount

    def _get_report_values(self, docids, data):
        wizard_id = data["wizard_id"]
        company = self.env["res.company"].browse(data["company_id"])
        company_id = data["company_id"]
        account_ids = data["account_ids"]
        partner_ids = data["partner_ids"]
        date_at = data["date_at"]
        date_at_object = datetime.strptime(date_at, "%Y-%m-%d").date()
        date_from = data["date_from"]
        target_move = data["target_move"]

        (
            move_lines_data,
            partners_data,
            journals_data,
            accounts_data,
            open_items_move_lines_data,
        ) = self._get_data(
            account_ids, partner_ids, date_at_object, target_move, company_id, date_from
        )

        total_amount = self._calculate_amounts(open_items_move_lines_data)
        return {
            "doc_ids": [wizard_id],
            "doc_model": "open.items.report.wizard",
            "docs": self.env["open.items.report.wizard"].browse(wizard_id),
            "foreign_currency": data["foreign_currency"],
            "company_name": company.display_name,
            "currency_name": company.currency_id.name,
            "date_at": date_at_object.strftime("%d/%m/%Y"),
            "hide_account_at_0": data["hide_account_at_0"],
            "target_move": data["target_move"],
            "partners_data": partners_data,
            "accounts_data": accounts_data,
            "total_amount": total_amount,
            "Open_Items": open_items_move_lines_data,
        }
