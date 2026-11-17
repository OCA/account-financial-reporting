# Author: Christopher Ormaza
# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import FORMATS


class ActivityStatementXslx(models.AbstractModel):
    _name = "report.p_s.report_activity_statement_xlsx"
    _description = "Activity Statement XLSL Report"
    _inherit = "report.p_s.report_statement_common_xlsx"

    def _get_report_label(self):
        return self.env._("Activity Statement")

    def _get_report_model_name(self):
        return "report.partner_statement.activity_statement"

    def _get_currency_header_row_data(self, partner, currency, data):
        return (
            [
                {
                    "col_pos": col_pos,
                    "sheet_func": "write",
                    "args": args,
                }
                for col_pos, args in enumerate(
                    [
                        (
                            self.env._("Reference Number"),
                            FORMATS["format_theader_yellow_center"],
                        ),
                        (self.env._("Date"), FORMATS["format_theader_yellow_center"]),
                    ]
                )
            ]
            + [
                {
                    "col_pos": 2,
                    "sheet_func": "merge_range",
                    "span": 1,
                    "args": (
                        self.env._("Description"),
                        FORMATS["format_theader_yellow_center"],
                    ),
                },
            ]
            + [
                {
                    "col_pos": col_pos,
                    "sheet_func": "write",
                    "args": args,
                }
                for col_pos, args in enumerate(
                    [
                        (
                            self.env._("Original Amount"),
                            FORMATS["format_theader_yellow_center"],
                        ),
                        (
                            self.env._("Applied Amount"),
                            FORMATS["format_theader_yellow_center"],
                        ),
                        (
                            self.env._("Open Amount"),
                            FORMATS["format_theader_yellow_center"],
                        ),
                    ],
                    4,
                )
            ]
        )

    def _get_currency_subheader_row_data(self, partner, currency, data):
        partner_data = data.get("data", {}).get(partner.id, {})
        currency_data = partner_data.get("currencies", {}).get(currency.id)
        return [
            {
                "col_pos": 1,
                "sheet_func": "write",
                "args": (
                    partner_data.get("prior_day"),
                    FORMATS["format_tcell_date_left"],
                ),
            },
            {
                "col_pos": 2,
                "sheet_func": "merge_range",
                "span": 3,
                "args": (self.env._("Balance Forward"), FORMATS["format_tcell_left"]),
            },
            {
                "col_pos": 6,
                "sheet_func": "write",
                "args": (
                    currency_data.get("balance_forward"),
                    FORMATS["current_money_format"],
                ),
            },
        ]

    def _write_currency_subheader(self, row_pos, sheet, partner, currency, data):
        row_pos += 1
        row_data = self._get_currency_subheader_row_data(partner, currency, data)
        self._write_row_data(sheet, row_pos, row_data)
        return row_pos

    def _get_currency_line_row_data(self, partner, currency, data, line):
        format_tcell_left = FORMATS["format_tcell_left"]
        format_tcell_date_left = FORMATS["format_tcell_date_left"]
        format_distributed = FORMATS["format_distributed"]
        current_money_format = FORMATS["current_money_format"]
        name_to_show = (
            line.get("name", "") == "/" or not line.get("name", "")
        ) and line.get("ref", "")
        if line.get("name", "") and line.get("name", "") != "/":
            if not line.get("ref", ""):
                name_to_show = line.get("name", "")
            else:
                if (line.get("name", "") in line.get("ref", "")) or (
                    line.get("name", "") == line.get("ref", "")
                ):
                    name_to_show = line.get("name", "")
                elif line.get("ref", "") not in line.get("name", ""):
                    name_to_show = line.get("ref", "")
        return (
            [
                {
                    "col_pos": col_pos,
                    "sheet_func": "write",
                    "args": args,
                }
                for col_pos, args in enumerate(
                    [
                        (line.get("move_id", ""), format_tcell_left),
                        (line.get("date", ""), format_tcell_date_left),
                    ]
                )
            ]
            + [
                {
                    "col_pos": 2,
                    "sheet_func": "merge_range",
                    "span": 1,
                    "args": (name_to_show, format_distributed),
                },
            ]
            + [
                {
                    "col_pos": col_pos,
                    "sheet_func": "write",
                    "args": args,
                }
                for col_pos, args in enumerate(
                    [
                        (line.get("amount", ""), current_money_format),
                        (line.get("applied_amount", ""), current_money_format),
                        (line.get("open_amount", ""), current_money_format),
                    ],
                    4,
                )
            ]
        )

    def _get_currency_title_kwargs(self, partner_data, account_type, currency):
        res = super()._get_currency_title_kwargs(partner_data, account_type, currency)
        res.update(
            {
                "is_detailed": False,
                "starting_date": partner_data.get("start"),
            }
        )
        return res
