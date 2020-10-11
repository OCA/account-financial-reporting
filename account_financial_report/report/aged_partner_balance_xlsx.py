# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class AgedPartnerBalanceXslx(models.AbstractModel):
    _name = "report.a_f_r.report_aged_partner_balance_xlsx"
    _description = "Aged Partner Balance XLSL Report"
    _inherit = "report.account_financial_report.abstract_report_xlsx"

    def _get_report_name(self, report, data=False):
        company_id = data.get("company_id", False)
        report_name = _("Aged Partner Balance")
        if company_id:
            company = self.env["res.company"].browse(company_id)
            suffix = " - {} - {}".format(company.name, company.currency_id.name)
            report_name = report_name + suffix
        return report_name

    def _get_report_columns(self, report):
        if not report.show_move_line_details:
            return {
                0: {"header": _("Partner"), "field": "name", "width": 70},
                1: {
                    "header": _("Residual"),
                    "field": "residual",
                    "field_footer_total": "residual",
                    "type": "amount",
                    "width": 14,
                },
                2: {
                    "header": _("Current"),
                    "field": "current",
                    "field_footer_total": "current",
                    "field_footer_percent": "percent_current",
                    "type": "amount",
                    "width": 14,
                },
                3: {
                    "header": _(u"Age ≤ 30 d."),
                    "field": "30_days",
                    "field_footer_total": "30_days",
                    "field_footer_percent": "percent_30_days",
                    "type": "amount",
                    "width": 14,
                },
                4: {
                    "header": _(u"Age ≤ 60 d."),
                    "field": "60_days",
                    "field_footer_total": "60_days",
                    "field_footer_percent": "percent_60_days",
                    "type": "amount",
                    "width": 14,
                },
                5: {
                    "header": _(u"Age ≤ 90 d."),
                    "field": "90_days",
                    "field_footer_total": "90_days",
                    "field_footer_percent": "percent_90_days",
                    "type": "amount",
                    "width": 14,
                },
                6: {
                    "header": _(u"Age ≤ 120 d."),
                    "field": "120_days",
                    "field_footer_total": "120_days",
                    "field_footer_percent": "percent_120_days",
                    "type": "amount",
                    "width": 14,
                },
                7: {
                    "header": _("Older"),
                    "field": "older",
                    "field_footer_total": "older",
                    "field_footer_percent": "percent_older",
                    "type": "amount",
                    "width": 14,
                },
            }
        return {
            0: {"header": _("Date"), "field": "date", "width": 11},
            1: {"header": _("Entry"), "field": "entry", "width": 18},
            2: {"header": _("Journal"), "field": "journal", "width": 8},
            3: {"header": _("Account"), "field": "account", "width": 9},
            4: {"header": _("Partner"), "field": "partner", "width": 25},
            5: {"header": _("Ref - Label"), "field": "ref_label", "width": 40},
            6: {"header": _("Due date"), "field": "due_date", "width": 11},
            7: {
                "header": _("Residual"),
                "field": "residual",
                "field_footer_total": "residual",
                "field_final_balance": "residual",
                "type": "amount",
                "width": 14,
            },
            8: {
                "header": _("Current"),
                "field": "current",
                "field_footer_total": "current",
                "field_footer_percent": "percent_current",
                "field_final_balance": "current",
                "type": "amount",
                "width": 14,
            },
            9: {
                "header": _(u"Age ≤ 30 d."),
                "field": "30_days",
                "field_footer_total": "30_days",
                "field_footer_percent": "percent_30_days",
                "field_final_balance": "30_days",
                "type": "amount",
                "width": 14,
            },
            10: {
                "header": _(u"Age ≤ 60 d."),
                "field": "60_days",
                "field_footer_total": "60_days",
                "field_footer_percent": "percent_60_days",
                "field_final_balance": "60_days",
                "type": "amount",
                "width": 14,
            },
            11: {
                "header": _(u"Age ≤ 90 d."),
                "field": "90_days",
                "field_footer_total": "90_days",
                "field_footer_percent": "percent_90_days",
                "field_final_balance": "90_days",
                "type": "amount",
                "width": 14,
            },
            12: {
                "header": _(u"Age ≤ 120 d."),
                "field": "120_days",
                "field_footer_total": "120_days",
                "field_footer_percent": "percent_120_days",
                "field_final_balance": "120_days",
                "type": "amount",
                "width": 14,
            },
            13: {
                "header": _("Older"),
                "field": "older",
                "field_footer_total": "older",
                "field_footer_percent": "percent_older",
                "field_final_balance": "older",
                "type": "amount",
                "width": 14,
            },
        }

    def _get_report_filters(self, report):
        return [
            [_("Date at filter"), report.date_at.strftime("%d/%m/%Y")],
            [
                _("Target moves filter"),
                _("All posted entries")
                if report.target_move == "posted"
                else _("All entries"),
            ],
        ]

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 3

    def _get_col_pos_footer_label(self, report):
        return 0 if not report.show_move_line_details else 5

    def _get_col_count_final_balance_name(self):
        return 5

    def _get_col_pos_final_balance_label(self):
        return 5

    def _generate_report_content(self, workbook, report, data):
        res_data = self.env[
            "report.account_financial_report.aged_partner_balance"
        ]._get_report_values(report, data)
        show_move_line_details = res_data["show_move_lines_details"]
        aged_partner_balance = res_data["aged_partner_balance"]
        if not show_move_line_details:
            # For each account
            for account in aged_partner_balance:
                # Write account title
                self.write_array_title(account["code"] + " - " + account["name"])

                # Display array header for partners lines
                self.write_array_header()

                # Display partner lines
                for partner in account["partners"]:
                    self.write_line_from_dict(partner)

                # Display account lines
                self.write_account_footer_from_dict(
                    report,
                    account,
                    ("Total"),
                    "field_footer_total",
                    self.format_header_right,
                    self.format_header_amount,
                    False,
                )
                self.write_account_footer_from_dict(
                    report,
                    account,
                    ("Percents"),
                    "field_footer_percent",
                    self.format_right_bold_italic,
                    self.format_percent_bold_italic,
                    True,
                )

                # 2 lines break
                self.row_pos += 2
        else:
            # For each account
            for account in aged_partner_balance:
                # Write account title
                self.write_array_title(account["code"] + " - " + account["name"])

                # For each partner
                for partner in account["partners"]:
                    # Write partner title
                    self.write_array_title(partner["name"])

                    # Display array header for move lines
                    self.write_array_header()

                    # Display account move lines
                    for line in partner["move_lines"]:
                        self.write_line_from_dict(line)

                    # Display ending balance line for partner
                    self.write_ending_balance_from_dict(partner)

                    # Line break
                    self.row_pos += 1

                # Display account lines
                self.write_account_footer_from_dict(
                    report,
                    account,
                    ("Total"),
                    "field_footer_total",
                    self.format_header_right,
                    self.format_header_amount,
                    False,
                )

                self.write_account_footer_from_dict(
                    report,
                    account,
                    ("Percents"),
                    "field_footer_percent",
                    self.format_right_bold_italic,
                    self.format_percent_bold_italic,
                    True,
                )

                # 2 lines break
                self.row_pos += 2

    def write_ending_balance_from_dict(self, my_object):
        """
        Specific function to write ending partner balance
        for Aged Partner Balance
        """
        name = None
        label = _("Partner cumul aged balance")
        super(AgedPartnerBalanceXslx, self).write_ending_balance_from_dict(
            my_object, name, label
        )

    def write_account_footer_from_dict(
        self,
        report,
        account,
        label,
        field_name,
        string_format,
        amount_format,
        amount_is_percent,
    ):
        """
        Specific function to write account footer for Aged Partner Balance
        """
        col_pos_footer_label = self._get_col_pos_footer_label(report)
        for col_pos, column in self.columns.items():
            if col_pos == col_pos_footer_label or column.get(field_name):
                if col_pos == col_pos_footer_label:
                    value = label
                else:
                    value = account.get(column[field_name], False)
                cell_type = column.get("type", "string")
                if cell_type == "string" or col_pos == col_pos_footer_label:
                    self.sheet.write_string(
                        self.row_pos, col_pos, value or "", string_format
                    )
                elif cell_type == "amount":
                    number = float(value)
                    if amount_is_percent:
                        number /= 100
                    self.sheet.write_number(
                        self.row_pos, col_pos, number, amount_format
                    )
            else:
                self.sheet.write_string(self.row_pos, col_pos, "", string_format)

        self.row_pos += 1
