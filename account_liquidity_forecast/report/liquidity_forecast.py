# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import calendar
import datetime

from odoo import _, fields, models
from odoo.tools.float_utils import float_is_zero
from odoo.tools.misc import format_date


class LiquidityForecastReport(models.AbstractModel):
    _name = "report.account_liquidity_forecast.liquidity_forecast"
    _description = "Liquidity Forecast Report"

    def _init_period(self, line, period):
        line["periods"][period["sequence"]] = {
            "amount": 0.0,
            "domain": "",
        }

    def _complete_liquidity_forecast_lines(
        self, data, liquidity_forecast_lines, line, period, periods
    ):
        if line["code"] == "cash_flow_line_out_payable":
            self._init_period(line, period)
            self._complete_cash_flow_lines_payable(
                data, liquidity_forecast_lines, period, periods
            )
        if line["code"] == "beginning_balance":
            self._init_period(line, period)
            self._complete_beginning_balance(
                data, liquidity_forecast_lines, line, period
            )
        if line["code"] == "ending_balance":
            self._init_period(line, period)
            self._complete_ending_balance(data, liquidity_forecast_lines, line, period)
        if line["code"] == "total_cash_inflows":
            self._init_period(line, period)
            self._complete_total_cash_inflows(
                data, liquidity_forecast_lines, line, period
            )
        if line["code"] == "total_cash_outflows":
            self._init_period(line, period)
            self._complete_total_cash_outflows(
                data, liquidity_forecast_lines, line, period
            )
        if line["code"] == "net_cash_flow":
            self._init_period(line, period)
            self._complete_net_cash_flow(data, liquidity_forecast_lines, line, period)
        return True

    def _complete_beginning_balance(self, data, liquidity_forecast_lines, line, period):
        if period["sequence"] == 0:
            domain = [
                ("account_id.account_type", "=", "asset_cash"),
                ("company_id", "=", data["company_id"]),
            ]
            if data["only_posted_moves"]:
                domain += [("move_id.state", "=", "posted")]
            else:
                domain += [("move_id.state", "in", ["posted", "draft"])]

            initial_balances = self.env["account.move.line"].read_group(
                domain=domain,
                fields=["balance:sum"],
                groupby=["company_id"],
            )
            initial_balance_amount = 0.0
            if initial_balances:
                initial_balance = initial_balances[0]
                initial_balance_amount = initial_balance["balance"]
            line["periods"][period["sequence"]]["amount"] = initial_balance_amount
        else:
            ending_balance_line = list(
                filter(
                    lambda d: d["code"] == "ending_balance", liquidity_forecast_lines
                )
            )
            line["periods"][period["sequence"]]["amount"] = ending_balance_line[0][
                "periods"
            ][period["sequence"] - 1]["amount"]

    def _complete_ending_balance(self, data, liquidity_forecast_lines, line, period):
        starting_balance_line = list(
            filter(lambda d: d["code"] == "beginning_balance", liquidity_forecast_lines)
        )[0]
        net_cash_flow_line = list(
            filter(lambda d: d["code"] == "net_cash_flow", liquidity_forecast_lines)
        )[0]
        line["periods"][period["sequence"]]["amount"] = (
            starting_balance_line["periods"][period["sequence"]]["amount"]
            + net_cash_flow_line["periods"][period["sequence"]]["amount"]
        )

    def _complete_total_cash_inflows(
        self, data, liquidity_forecast_lines, line, period
    ):
        cash_inflow = 0.0
        cash_inflow_lines = list(
            filter(lambda d: "cash_flow_line_in" in d["code"], liquidity_forecast_lines)
        )
        for cash_inflow_line in cash_inflow_lines:
            cash_inflow += cash_inflow_line["periods"][period["sequence"]]["amount"]
        line["periods"][period["sequence"]]["amount"] = cash_inflow

    def _complete_total_cash_outflows(
        self, data, liquidity_forecast_lines, line, period
    ):
        cash_outflow = 0.0
        cash_outflow_lines = list(
            filter(
                lambda d: "cash_flow_line_out" in d["code"], liquidity_forecast_lines
            )
        )
        for cash_outflow_line in cash_outflow_lines:
            cash_outflow += cash_outflow_line["periods"][period["sequence"]]["amount"]
        line["periods"][period["sequence"]]["amount"] = cash_outflow

    def _complete_net_cash_flow(self, data, liquidity_forecast_lines, line, period):
        cash_flow = 0.0
        cash_flow_lines = list(
            filter(lambda d: "cash_flow_line" in d["code"], liquidity_forecast_lines)
        )
        for cash_flow_line in cash_flow_lines:
            cash_flow += cash_flow_line["periods"][period["sequence"]]["amount"]
        line["periods"][period["sequence"]]["amount"] = cash_flow

    def _prepare_cash_flow_lines(
        self, data, liquidity_forecast_lines, period, periods, accounts, date_type
    ):
        company_id = data.get("company_id", self.env.user.company_id.id)
        company = self.env["res.company"].browse(company_id)
        open_amls = accounts._get_open_items_at_date(
            period["date_to"], data["only_posted_moves"]
        )
        period_open_amls = self.env["account.move.line"]
        rounding = company.currency_id.rounding
        for open_aml in open_amls:
            date_due = open_aml[date_type] or open_aml["date"]
            if (
                (
                    (period["sequence"] == 0 and period["date_to"] >= date_due)
                    or not date_due
                )
                or (
                    period["sequence"] > 0
                    and period["date_to"] >= date_due >= period["date_from"]
                )
            ) and not float_is_zero(
                open_aml.amount_residual, precision_rounding=rounding
            ):
                period_open_amls |= open_aml
        in_flows = {}
        out_flows = {}
        for open_aml in period_open_amls:
            account = open_aml.account_id
            open_item_amount = open_aml.amount_residual
            if open_item_amount > 0 and account not in in_flows.keys():
                in_flows[account] = {"amount": 0.0, "move_line_ids": []}
            if open_item_amount < 0 and account not in out_flows.keys():
                out_flows[account] = {"amount": 0.0, "move_line_ids": []}
            if open_item_amount > 0:
                in_flows[account]["amount"] += open_item_amount
                in_flows[account]["move_line_ids"].append(open_aml.id)
            else:
                out_flows[account]["amount"] += open_item_amount
                out_flows[account]["move_line_ids"].append(open_aml.id)
        for account in in_flows.keys():
            in_cash_flow_lines = list(
                filter(
                    lambda d: "cash_flow_line_%s_account_%s" % ("in", account.code)
                    in d["code"],
                    liquidity_forecast_lines,
                )
            )
            if not in_cash_flow_lines:
                in_cash_flow_line = {
                    "code": "cash_flow_line_%s_account_%s" % ("in", account.code),
                    "type": "amount",
                    "level": "detail",
                    "model": "account.move.line",
                    "title": account.display_name,
                    "periods": {},
                    "sequence": 1100,
                }
                for p in periods:
                    in_cash_flow_line["periods"][p["sequence"]] = {
                        "amount": 0.0,
                        "domain": "",
                    }
                liquidity_forecast_lines.append(in_cash_flow_line)
            else:
                in_cash_flow_line = in_cash_flow_lines[0]
            in_cash_flow_line["periods"][period["sequence"]]["amount"] += in_flows[
                account
            ]["amount"]
            in_cash_flow_line["periods"][period["sequence"]]["domain"] = [
                ("id", "in", in_flows[account]["move_line_ids"])
            ]
        for account in out_flows.keys():
            out_cash_flow_lines = list(
                filter(
                    lambda d: "cash_flow_line_%s_account_%s" % ("out", account.code)
                    in d["code"],
                    liquidity_forecast_lines,
                )
            )
            if not out_cash_flow_lines:
                out_cash_flow_line = {
                    "code": "cash_flow_line_%s_account_%s" % ("out", account.code),
                    "type": "amount",
                    "level": "detail",
                    "model": "account.move.line",
                    "title": account.display_name,
                    "periods": {},
                    "sequence": 3100,
                }
                for p in periods:
                    out_cash_flow_line["periods"][p["sequence"]] = {
                        "amount": 0.0,
                        "domain": "",
                    }
                liquidity_forecast_lines.append(out_cash_flow_line)
            else:
                out_cash_flow_line = out_cash_flow_lines[0]
            out_cash_flow_line["periods"][period["sequence"]]["amount"] += out_flows[
                account
            ]["amount"]
            out_cash_flow_line["periods"][period["sequence"]]["domain"] = [
                ("id", "in", out_flows[account]["move_line_ids"])
            ]

    def _prepare_cash_flow_lines_move_line(
        self,
        data,
        liquidity_forecast_lines,
        period,
        periods,
    ):
        accounts = self.env["account.account"].search(
            [
                ("account_type", "in", ["asset_receivable", "liability_payable"]),
                ("company_id", "=", data["company_id"]),
            ]
        )
        self._prepare_cash_flow_lines(
            data, liquidity_forecast_lines, period, periods, accounts, "date_maturity"
        )

    def _prepare_cash_flow_lines_payment(
        self, data, liquidity_forecast_lines, period, periods
    ):
        company_id = data.get("company_id", self.env.user.company_id.id)
        company = self.env["res.company"].browse(company_id)
        bank_journals = self.env["account.journal"].search(
            [
                ("type", "=", "bank"),
                ("company_id", "=", company.id),
            ]
        )
        accounts = self.env["account.account"]
        for bank_journal in bank_journals:
            accounts += bank_journal._get_journal_inbound_outstanding_payment_accounts()
            accounts += (
                bank_journal._get_journal_outbound_outstanding_payment_accounts()
            )
        self._prepare_cash_flow_lines(
            data, liquidity_forecast_lines, period, periods, accounts, "date"
        )

    def _prepare_cash_flow_lines_payment_planning_item(
        self, data, liquidity_forecast_lines, period, periods, direction="in"
    ):
        company_id = data.get("company_id", self.env.user.company_id.id)
        domain = [
            ("company_id", "=", company_id),
            ("date", "<=", period["date_to"]),
            ("direction", "=", direction),
            ("expiry_date", ">=", fields.Date.today()),
        ]
        if period["sequence"] > 0:
            domain += [("date", ">=", period["date_from"])]
        totals = self.env["account.liquidity.forecast.planning.item"].read_group(
            domain=domain,
            fields=["amount:sum"],
            groupby=["group_id"],
        )
        for total in totals:
            group_id = total["group_id"] and total["group_id"][0] or False
            group_name = ""
            group = self.env["account.liquidity.forecast.planning.group"]
            if group_id:
                group = self.env["account.liquidity.forecast.planning.group"].browse(
                    group_id
                )
                group_name = group and group.name or ""
            title = group_name or _("Forecast Planning Items")
            code = "cash_flow_line_%s_planned_item" % direction
            if group:
                code = "%s_%s" % (code, group_name)
            cash_flow_lines = list(
                filter(
                    lambda d: code in d["code"],
                    liquidity_forecast_lines,
                )
            )
            if not cash_flow_lines:
                cash_flow_line = {
                    "code": code,
                    "type": "amount",
                    "level": "detail",
                    "model": "account.liquidity.forecast.planning.item",
                    "title": title,
                    "periods": {},
                }
                if direction == "in":
                    cash_flow_line["sequence"] = 1200
                else:
                    cash_flow_line["sequence"] = 3200
                for p in periods:
                    cash_flow_line["periods"][p["sequence"]] = {
                        "amount": 0.0,
                        "domain": "",
                    }
                liquidity_forecast_lines.append(cash_flow_line)
            else:
                cash_flow_line = cash_flow_lines[0]
            sign = direction == "in" and 1 or -1
            cash_flow_line["periods"][period["sequence"]]["amount"] += (
                total["amount"] * sign
            )
            cash_flow_line["periods"][period["sequence"]]["domain"] = total["__domain"]

    def _prepare_cash_flow_lines_payment_planning_item_in(
        self, data, liquidity_forecast_lines, period, periods
    ):
        self._prepare_cash_flow_lines_payment_planning_item(
            data, liquidity_forecast_lines, period, periods, direction="in"
        )

    def _prepare_cash_flow_lines_payment_planning_item_out(
        self, data, liquidity_forecast_lines, period, periods
    ):
        self._prepare_cash_flow_lines_payment_planning_item(
            data, liquidity_forecast_lines, period, periods, direction="out"
        )

    def _generate_periods(self, data):
        date_from = fields.Date.from_string(data["date_from"])
        date_to = fields.Date.from_string(data["date_to"])
        period_length = data["period_length"]
        periods = []
        current_date = date_from
        sequence = 0

        while current_date <= date_to:
            if period_length == "days":
                name = format_date(self.env, current_date)
                period_end = current_date

            elif period_length == "weeks":
                lang = self.env.company.partner_id.lang
                lang_obj = self.env["res.lang"].search([("code", "=", lang)], limit=1)
                week_start_day = int(lang_obj.week_start or "7")

                days_from_week_start = (current_date.weekday() - week_start_day) % 7
                week_start = current_date - datetime.timedelta(
                    days=days_from_week_start
                )
                week_end = week_start + datetime.timedelta(days=6)

                period_end = week_end
                current_date = week_start
                week_number = week_start.isocalendar()[1]

                name = (
                    f"Week {week_number} ({format_date(self.env, week_start)} -"
                    f" {format_date(self.env, week_end)})"
                )

            elif period_length == "months":
                _x, last_day = calendar.monthrange(
                    current_date.year, current_date.month
                )
                period_end = datetime.date(
                    current_date.year, current_date.month, last_day
                )
                name = format_date(self.env, current_date, date_format="MMMM yyyy")

            if sequence == 0:
                name = _("Current %s") % name

            period = {
                "sequence": sequence,
                "name": name,
                "date_from": current_date,
                "date_to": min(period_end, date_to),
            }
            periods.append(period)
            sequence += 1
            current_date = period["date_to"] + datetime.timedelta(days=1)

        return periods

    def _prepare_liquidity_forecast_lines_period(
        self, data, liquidity_forecast_lines, period, periods
    ):
        """Extend with your own methods"""
        self._prepare_cash_flow_lines_move_line(
            data, liquidity_forecast_lines, period, periods
        )
        self._prepare_cash_flow_lines_payment(
            data, liquidity_forecast_lines, period, periods
        )
        self._prepare_cash_flow_lines_payment_planning_item_in(
            data, liquidity_forecast_lines, period, periods
        )
        self._prepare_cash_flow_lines_payment_planning_item_out(
            data, liquidity_forecast_lines, period, periods
        )
        return True

    def _prepare_liquidity_forecast_lines(self, data):
        periods = self._generate_periods(data)
        liquidity_forecast_lines = [
            {
                "code": "beginning_balance",
                "type": "amount",
                "level": "heading",
                "model": "",
                "title": _("BEGINNING BALANCE"),
                "sequence": 10,
                "periods": {},
            },
            {
                "code": "cash_inflows",
                "type": "text",
                "level": "heading",
                "model": "",
                "title": _("CASH INFLOWS"),
                "sequence": 1000,
                "periods": {},
            },
            {
                "code": "total_cash_inflows",
                "type": "amount",
                "level": "heading",
                "model": "",
                "title": _("Total Cash Inflows"),
                "sequence": 2000,
                "periods": {},
            },
            {
                "code": "cash_outflows",
                "type": "text",
                "level": "heading",
                "model": "",
                "title": _("CASH OUTFLOWS"),
                "sequence": 3000,
                "periods": {},
            },
            {
                "code": "total_cash_outflows",
                "type": "amount",
                "level": "heading",
                "domain": "",
                "model": "",
                "title": _("Total Cash Outflows"),
                "sequence": 4000,
                "periods": {},
            },
            {
                "code": "net_cash_flow",
                "type": "amount",
                "level": "heading",
                "domain": "",
                "model": "",
                "title": _("NET CASH FLOW"),
                "sequence": 5000,
                "periods": {},
            },
            {
                "code": "ending_balance",
                "type": "amount",
                "level": "heading",
                "domain": "",
                "model": "",
                "title": _("ENDING BALANCE"),
                "sequence": 6000,
                "periods": {},
            },
        ]
        for period in periods:
            self._prepare_liquidity_forecast_lines_period(
                data, liquidity_forecast_lines, period, periods
            )
            for line in liquidity_forecast_lines:
                self._complete_liquidity_forecast_lines(
                    data, liquidity_forecast_lines, line, period, periods
                )
        liquidity_forecast_lines = sorted(
            liquidity_forecast_lines, key=lambda x: x["sequence"]
        )
        return liquidity_forecast_lines, periods

    def _get_report_values(self, docids, data):
        wizard_id = data["wizard_id"]
        company = self.env["res.company"].browse(data["company_id"])
        liquidity_forecast_lines, periods = self._prepare_liquidity_forecast_lines(data)

        return {
            "doc_ ids": [wizard_id],
            "doc_model": "liquidity.forecast.report.wizard",
            "docs": self.env["account.liquidity.forecast.report.wizard"].browse(
                wizard_id
            ),
            "company_name": company.display_name,
            "company_currency": company.currency_id,
            "currency_name": company.currency_id.name,
            "date_from": data["date_from"],
            "date_to": data["date_to"],
            "only_posted_moves": data["only_posted_moves"],
            "liquidity_forecast_lines": liquidity_forecast_lines,
            "periods": periods,
        }
