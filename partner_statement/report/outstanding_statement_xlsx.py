# Author: Christopher Ormaza
# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import FORMATS


class OutstandingStatementXslx(models.AbstractModel):
    _name = "report.p_s.report_outstanding_statement_xlsx"
    _description = "Outstanding Statement XLSL Report"
    _inherit = "report.p_s.report_statement_common_xlsx"

    def _get_report_label(self):
        return self.env._("Outstanding Statement")

    def _get_report_model_name(self):
        return "report.partner_statement.outstanding_statement"

    def _get_currency_header_row_data(self, partner, currency, data):
        return [
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
                    (self.env._("Due Date"), FORMATS["format_theader_yellow_center"]),
                    (
                        self.env._("Description"),
                        FORMATS["format_theader_yellow_center"],
                    ),
                    (self.env._("Original"), FORMATS["format_theader_yellow_center"]),
                    (
                        self.env._("Open Amount"),
                        FORMATS["format_theader_yellow_center"],
                    ),
                    (self.env._("Balance"), FORMATS["format_theader_yellow_center"]),
                ]
            )
        ]

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
                if (line.get("ref", "") in line.get("name", "")) or (
                    line.get("name", "") == line.get("ref", "")
                ):
                    name_to_show = line.get("name", "")
                else:
                    name_to_show = line.get("ref", "")
        return [
            {
                "col_pos": col_pos,
                "sheet_func": "write",
                "args": args,
            }
            for col_pos, args in enumerate(
                [
                    (line.get("move_id", ""), format_tcell_left),
                    (line.get("date", ""), format_tcell_date_left),
                    (line.get("date_maturity", ""), format_tcell_date_left),
                    (name_to_show, format_distributed),
                    (line.get("amount", ""), current_money_format),
                    (line.get("open_amount", ""), current_money_format),
                    (line.get("balance", ""), current_money_format),
                ]
            )
        ]
