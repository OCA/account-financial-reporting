# Author: Damien Crier
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class GeneralLedgerXslx(models.AbstractModel):
    _name = "report.a_f_r.report_general_ledger_xlsx"
    _description = "General Ledger XLSL Report"
    _inherit = "report.account_financial_report.abstract_report_xlsx"

    def _get_report_name(self, report, data=False):
        company_id = data.get("company_id", False)
        report_name = _("General Ledger")
        if company_id:
            company = self.env["res.company"].browse(company_id)
            suffix = " - {} - {}".format(company.name, company.currency_id.name)
            report_name = report_name + suffix
        return report_name

    def _get_report_columns(self, report):
        res = [
            {"header": _("Date"), "field": "date", "width": 11},
            {"header": _("Entry"), "field": "entry", "width": 18},
            {"header": _("Journal"), "field": "journal", "width": 8},
            {"header": _("Account"), "field": "account", "width": 9},
            {"header": _("Taxes"), "field": "taxes_description", "width": 15},
            {"header": _("Partner"), "field": "partner_name", "width": 25},
            {"header": _("Ref - Label"), "field": "ref_label", "width": 40},
        ]
        if report.show_cost_center:
            res += [
                {
                    "header": _("Analytic Account"),
                    "field": "analytic_account",
                    "width": 20,
                },
            ]
        if report.show_analytic_tags:
            res += [
                {"header": _("Tags"), "field": "tags", "width": 10},
            ]
        res += [
            {"header": _("Rec."), "field": "rec_name", "width": 15},
            {
                "header": _("Debit"),
                "field": "debit",
                "field_initial_balance": "initial_debit",
                "field_final_balance": "final_debit",
                "type": "amount",
                "width": 14,
            },
            {
                "header": _("Credit"),
                "field": "credit",
                "field_initial_balance": "initial_credit",
                "field_final_balance": "final_credit",
                "type": "amount",
                "width": 14,
            },
            {
                "header": _("Cumul. Bal."),
                "field": "balance",
                "field_initial_balance": "initial_balance",
                "field_final_balance": "final_balance",
                "type": "amount",
                "width": 14,
            },
        ]
        if report.foreign_currency:
            res += [
                {
                    "header": _("Cur."),
                    "field": "currency_name",
                    "field_currency_balance": "currency_name",
                    "type": "currency_name",
                    "width": 7,
                },
                {
                    "header": _("Amount cur."),
                    "field": "bal_curr",
                    "field_initial_balance": "initial_bal_curr",
                    "field_final_balance": "final_bal_curr",
                    "type": "amount_currency",
                    "width": 14,
                },
            ]
        res_as_dict = {}
        for i, column in enumerate(res):
            res_as_dict[i] = column
        return res_as_dict

    def _get_report_filters(self, report):
        return [
            [
                _("Date range filter"),
                _("From: %s To: %s") % (report.date_from, report.date_to),
            ],
            [
                _("Target moves filter"),
                _("All posted entries")
                if report.target_move == "posted"
                else _("All entries"),
            ],
            [
                _("Account balance at 0 filter"),
                _("Hide") if report.hide_account_at_0 else _("Show"),
            ],
            [_("Centralize filter"), _("Yes") if report.centralize else _("No")],
            [
                _("Show analytic tags"),
                _("Yes") if report.show_analytic_tags else _("No"),
            ],
            [
                _("Show foreign currency"),
                _("Yes") if report.foreign_currency else _("No"),
            ],
        ]

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 2

    def _get_col_pos_initial_balance_label(self):
        return 5

    def _get_col_count_final_balance_name(self):
        return 5

    def _get_col_pos_final_balance_label(self):
        return 5

    # flake8: noqa: C901
    def _generate_report_content(self, workbook, report, data):
        res_data = self.env[
            "report.account_financial_report.general_ledger"
        ]._get_report_values(report, data)
        general_ledger = res_data["general_ledger"]
        accounts_data = res_data["accounts_data"]
        partners_data = res_data["partners_data"]
        journals_data = res_data["journals_data"]
        taxes_data = res_data["taxes_data"]
        tags_data = res_data["tags_data"]
        filter_partner_ids = res_data["filter_partner_ids"]
        foreign_currency = res_data["foreign_currency"]
        # For each account
        for account in general_ledger:
            # Write account title
            self.write_array_title(
                account["code"] + " - " + accounts_data[account["id"]]["name"]
            )

            if not account["partners"]:
                # Display array header for move lines
                self.write_array_header()

                # Display initial balance line for account
                account.update(
                    {
                        "initial_debit": account["init_bal"]["debit"],
                        "initial_credit": account["init_bal"]["credit"],
                        "initial_balance": account["init_bal"]["balance"],
                    }
                )
                if foreign_currency:
                    account.update(
                        {"initial_bal_curr": account["init_bal"]["bal_curr"]}
                    )
                self.write_initial_balance_from_dict(account)

                # Display account move lines
                for line in account["move_lines"]:
                    line.update(
                        {
                            "account": account["code"],
                            "journal": journals_data[line["journal_id"]]["code"],
                        }
                    )
                    if line["currency_id"]:
                        line.update(
                            {
                                "currency_name": line["currency_id"][1],
                                "currency_id": line["currency_id"][0],
                            }
                        )
                    if line["ref_label"] != "Centralized entries":
                        taxes_description = ""
                        tags = ""
                        for tax_id in line["tax_ids"]:
                            taxes_description += taxes_data[tax_id]["tax_name"] + " "
                        for tag_id in line["tag_ids"]:
                            tags += tags_data[tag_id]["name"] + " "
                        line.update(
                            {"taxes_description": taxes_description, "tags": tags,}
                        )
                    self.write_line_from_dict(line)
                # Display ending balance line for account
                account.update(
                    {
                        "final_debit": account["fin_bal"]["debit"],
                        "final_credit": account["fin_bal"]["credit"],
                        "final_balance": account["fin_bal"]["balance"],
                    }
                )
                if foreign_currency:
                    account.update(
                        {"final_bal_curr": account["fin_bal"]["bal_curr"],}
                    )
                self.write_ending_balance_from_dict(account)

            else:
                # For each partner
                for partner in account["list_partner"]:
                    # Write partner title
                    self.write_array_title(partners_data[partner["id"]]["name"])

                    # Display array header for move lines
                    self.write_array_header()

                    # Display initial balance line for partner
                    partner.update(
                        {
                            "initial_debit": partner["init_bal"]["debit"],
                            "initial_credit": partner["init_bal"]["credit"],
                            "initial_balance": partner["init_bal"]["balance"],
                            "name": partners_data[partner["id"]]["name"],
                            "type": "partner",
                            "currency_id": accounts_data[account["id"]]["currency_id"],
                        }
                    )
                    if foreign_currency:
                        partner.update(
                            {"initial_bal_curr": partner["init_bal"]["bal_curr"],}
                        )
                    self.write_initial_balance_from_dict(partner)

                    # Display account move lines
                    for line in partner["move_lines"]:
                        line.update(
                            {
                                "account": account["code"],
                                "journal": journals_data[line["journal_id"]]["code"],
                            }
                        )
                        if line["currency_id"]:
                            line.update(
                                {
                                    "currency_name": line["currency_id"][1],
                                    "currency_id": line["currency_id"][0],
                                }
                            )
                        if line["ref_label"] != "Centralized entries":
                            taxes_description = ""
                            tags = ""
                            for tax_id in line["tax_ids"]:
                                taxes_description += (
                                    taxes_data[tax_id]["tax_name"] + " "
                                )
                            for tag_id in line["tag_ids"]:
                                tags += tags_data[tag_id]["name"] + " "
                            line.update(
                                {"taxes_description": taxes_description, "tags": tags,}
                            )
                        self.write_line_from_dict(line)

                    # Display ending balance line for partner
                    partner.update(
                        {
                            "final_debit": partner["fin_bal"]["debit"],
                            "final_credit": partner["fin_bal"]["credit"],
                            "final_balance": partner["fin_bal"]["balance"],
                        }
                    )
                    if foreign_currency and partner["currency_id"]:
                        partner.update(
                            {
                                "final_bal_curr": partner["fin_bal"]["bal_curr"],
                                "currency_name": partner["currency_id"].name,
                                "currency_id": partner["currency_id"].id,
                            }
                        )
                    self.write_ending_balance_from_dict(partner)

                    # Line break
                    self.row_pos += 1

                if not filter_partner_ids:
                    account.update(
                        {
                            "final_debit": account["fin_bal"]["debit"],
                            "final_credit": account["fin_bal"]["credit"],
                            "final_balance": account["fin_bal"]["balance"],
                        }
                    )
                    if foreign_currency and account["currency_id"]:
                        account.update(
                            {
                                "final_bal_curr": account["fin_bal"]["bal_curr"],
                                "currency_name": account["currency_id"].name,
                                "currency_id": account["currency_id"].id,
                            }
                        )
                    self.write_ending_balance_from_dict(account)

            # 2 lines break
            self.row_pos += 2

    def write_initial_balance_from_dict(self, my_object):
        """Specific function to write initial balance for General Ledger"""
        if "partner" in my_object["type"]:
            label = _("Partner Initial balance")
        elif "account" in my_object["type"]:
            label = _("Initial balance")
        super(GeneralLedgerXslx, self).write_initial_balance_from_dict(my_object, label)

    def write_ending_balance_from_dict(self, my_object):
        """Specific function to write ending balance for General Ledger"""
        if "partner" in my_object["type"]:
            name = my_object["name"]
            label = _("Partner ending balance")
        elif "account" in my_object["type"]:
            name = my_object["code"] + " - " + my_object["name"]
            label = _("Ending balance")
        super(GeneralLedgerXslx, self).write_ending_balance_from_dict(
            my_object, name, label
        )
