# Author: Jasmin Solanki
# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import FORMATS


def copy_format(book, fmt):
    properties = [f[4:] for f in dir(fmt) if f[0:4] == "set_"]
    dft_fmt = book.add_format()
    return book.add_format(
        {
            k: v
            for k, v in fmt.__dict__.items()
            if k in properties and dft_fmt.__dict__[k] != v
        }
    )


class LiquidityForecastXslx(models.AbstractModel):
    _name = "report.report_liquidity_forecast_xlsx"
    _description = "Liquidity Forecast Report"
    _inherit = "report.report_xlsx.abstract"

    def _get_report_name(self, report, data=False):
        company_id = data.get("company_id", False)
        report_name = _("Liquidity Forecast")
        if company_id:
            company = self.env["res.company"].browse(company_id)
            suffix = " - {} - {}".format(company.name, company.currency_id.name)
            report_name = report_name + suffix
        return report_name

    def excel_column_name(self, column_number):
        alphabet = ""
        while column_number > 0:
            remainder = (column_number - 1) % 26
            alphabet = chr(65 + remainder) + alphabet
            column_number = (column_number - 1) // 26
        return alphabet

    def _size_columns(self, sheet, total_col_count, data):
        for i in range(total_col_count + 1):
            if i == 0:
                sheet.set_column("A:A", 30)
            else:
                sheet.set_column(
                    "%(col)s:%(col)s" % ({"col": self.excel_column_name(i + 1)}), 15
                )

    def generate_xlsx_report(self, workbook, data, objects):
        self._define_formats(workbook)
        report_data = self.env[
            "report.account_liquidity_forecast.liquidity_forecast"
        ]._get_report_values(objects.ids, data)
        FORMATS["format_ws_title_center"] = workbook.add_format(
            {"bold": True, "font_size": 14, "align": "center"}
        )
        company_id = data.get("company_id", False)
        if company_id:
            company = self.env["res.company"].browse(company_id)
        else:
            company = self.env.user.company_id
        currency = report_data["company_currency"]
        if currency.position == "after":
            money_string = "#,##0.%s " % (
                "0" * currency.decimal_places
            ) + "[${}]".format(currency.symbol)
        elif currency.position == "before":
            money_string = "[${}]".format(currency.symbol) + " #,##0.%s" % (
                "0" * currency.decimal_places
            )
        FORMATS["money_format"] = workbook.add_format({"num_format": money_string})
        FORMATS["money_format_bold"] = workbook.add_format(
            {"num_format": money_string, "bold": True}
        )
        FORMATS["format_center_bold"].text_wrap = 1
        FORMATS["format_center"].text_wrap = 1
        sheet = workbook.add_worksheet(_("Liquidity Forecast"))
        sheet.set_landscape()
        total_col_count = len(report_data["periods"])
        self._size_columns(sheet, total_col_count, data)
        row_pos = 0
        sheet.merge_range(
            row_pos,
            0,
            row_pos,
            4,
            _("Liquidity Forecast - %(company_name)s - %(currency_name)s")
            % (
                {
                    "company_name": company.display_name,
                    "currency_name": report_data["currency_name"],
                }
            ),
            FORMATS["format_ws_title_center"],
        )
        row_pos += 1
        sheet.merge_range(
            row_pos,
            0,
            row_pos,
            2,
            _("Date range filter"),
            FORMATS["format_theader_yellow_center"],
        )
        sheet.merge_range(
            row_pos,
            3,
            row_pos,
            4,
            _("Target moves filter"),
            FORMATS["format_theader_yellow_center"],
        )
        row_pos += 1
        sheet.merge_range(
            row_pos,
            0,
            row_pos,
            2,
            "From %s To %s" % (report_data["date_from"], report_data["date_to"]),
            FORMATS["format_center"],
        )
        sheet.merge_range(
            row_pos,
            3,
            row_pos,
            4,
            "All posted entries" if report_data["only_posted_moves"] else "All entries",
            FORMATS["format_center"],
        )
        row_pos += 1
        sheet.write(
            row_pos,
            0,
            "Items",
            FORMATS["format_center_bold"],
        )
        col = 1
        for period in report_data["periods"]:
            sheet.write(
                row_pos,
                col,
                period["name"],
                FORMATS["format_center_bold"],
            )
            col += 1
        row_pos += 1
        for line in report_data["liquidity_forecast_lines"]:
            sheet.write(
                row_pos,
                0,
                line["title"],
                (
                    FORMATS["format_left_bold"]
                    if line.get("level") == "heading"
                    else FORMATS["format_left"]
                ),
            )
            col = 1
            for period in line["periods"].values():
                sheet.write(
                    row_pos,
                    col,
                    period["amount"],
                    (
                        FORMATS["money_format_bold"]
                        if line.get("level") == "heading"
                        else FORMATS["money_format"]
                    ),
                )
                col += 1
            row_pos += 1
