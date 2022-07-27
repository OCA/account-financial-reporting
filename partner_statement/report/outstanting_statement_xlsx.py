# Author: Christopher Ormaza
# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models


class OutstandingStatementXslx(models.AbstractModel):
    _name = "report.p_s.report_outstanding_statement_xlsx"
    _description = "Outstanding Statement XLSL Report"
    _inherit = "report.report_xlsx.abstract"

    def _get_report_name(self, report, data=False):
        company_id = data.get("company_id", False)
        report_name = _("Outstanding Statement")
        if company_id:
            company = self.env["res.company"].browse(company_id)
            suffix = " - {} - {}".format(company.name, company.currency_id.name)
            report_name = report_name + suffix
        return report_name

    def _write_currency_lines(self, row_pos, sheet, partner, currency, data):
        partner_data = data.get("data", {}).get(partner.id, {})
        currency_data = partner_data.get("currencies", {}).get(currency.id)
        account_type = data.get("account_type", False)
        row_pos += 2
        statement_header = _(
            "%sStatement up to %s in %s"
            % (
                account_type == "payable" and _("Supplier ") or "",
                partner_data.get("end"),
                currency.display_name,
            )
        )
        sheet.merge_range(
            row_pos, 0, row_pos, 6, statement_header, self.format_right_bold
        )
        row_pos += 1
        sheet.write(
            row_pos, 0, _("Reference Number"), self.format_theader_yellow_center
        )
        sheet.write(row_pos, 1, _("Date"), self.format_theader_yellow_center)
        sheet.write(row_pos, 2, _("Due Date"), self.format_theader_yellow_center)
        sheet.write(row_pos, 3, _("Description"), self.format_theader_yellow_center)
        sheet.write(row_pos, 4, _("Original"), self.format_theader_yellow_center)
        sheet.write(row_pos, 5, _("Open Amount"), self.format_theader_yellow_center)
        sheet.write(row_pos, 6, _("Balance"), self.format_theader_yellow_center)
        for line in currency_data.get("lines"):
            row_pos += 1
            name_to_show = (
                line.get("name", "") == "/" or not line.get("name", "")
            ) and line.get("ref", "")
            if line.get("name", "") != "/":
                if not line.get("ref", ""):
                    name_to_show = line.get("name", "")
                else:
                    if (line.get("name", "") in line.get("ref", "")) or (
                        line.get("name", "") == line.get("ref", "")
                    ):
                        name_to_show = line.get("name", "")
                    elif line.get("ref", "") not in line.get("name", ""):
                        name_to_show = line.get("ref", "")
            sheet.write(row_pos, 0, line.get("move_id", ""), self.format_tcell_left)
            sheet.write(row_pos, 1, line.get("date", ""), self.format_tcell_date_left)
            sheet.write(
                row_pos, 2, line.get("date_maturity", ""), self.format_tcell_date_left
            )
            sheet.write(row_pos, 3, name_to_show, self.format_distributed)
            sheet.write(row_pos, 4, line.get("amount", ""), self.current_money_format)
            sheet.write(
                row_pos, 5, line.get("open_amount", ""), self.current_money_format
            )
            sheet.write(row_pos, 6, line.get("balance", ""), self.current_money_format)
        row_pos += 1
        sheet.write(row_pos, 1, partner_data.get("end"), self.format_tcell_date_left)
        sheet.merge_range(
            row_pos, 2, row_pos, 4, _("Ending Balance"), self.format_tcell_left
        )
        sheet.write(
            row_pos, 6, currency_data.get("amount_due"), self.current_money_format
        )
        return row_pos

    def _write_currency_buckets(self, row_pos, sheet, partner, currency, data):
        report_model = self.env["report.partner_statement.outstanding_statement"]
        partner_data = data.get("data", {}).get(partner.id, {})
        currency_data = partner_data.get("currencies", {}).get(currency.id)
        if currency_data.get("buckets"):
            row_pos += 2
            buckets_header = _("Aging Report at %s in %s") % (
                partner_data.get("end"),
                currency.display_name,
            )
            sheet.merge_range(
                row_pos, 0, row_pos, 6, buckets_header, self.format_right_bold
            )
            buckets_data = currency_data.get("buckets")
            buckets_labels = report_model._get_bucket_labels(
                partner_data.get("end"), data.get("aging_type")
            )
            row_pos += 1
            for i in range(len(buckets_labels)):
                sheet.write(
                    row_pos, i, buckets_labels[i], self.format_theader_yellow_center
                )
            row_pos += 1
            sheet.write(
                row_pos, 0, buckets_data.get("current", 0.0), self.current_money_format
            )
            sheet.write(
                row_pos, 1, buckets_data.get("b_1_30", 0.0), self.current_money_format
            )
            sheet.write(
                row_pos, 2, buckets_data.get("b_30_60", 0.0), self.current_money_format
            )
            sheet.write(
                row_pos, 3, buckets_data.get("b_60_90", 0.0), self.current_money_format
            )
            sheet.write(
                row_pos, 4, buckets_data.get("b_90_120", 0.0), self.current_money_format
            )
            sheet.write(
                row_pos,
                5,
                buckets_data.get("b_over_120", 0.0),
                self.current_money_format,
            )
            sheet.write(
                row_pos, 6, buckets_data.get("balance", 0.0), self.current_money_format
            )
        return row_pos

    def _size_columns(self, sheet):
        for i in range(7):
            sheet.set_column(0, i, 20)

    def generate_xlsx_report(self, workbook, data, objects):
        report_model = self.env["report.partner_statement.outstanding_statement"]
        self._define_formats(workbook)
        self.format_distributed = workbook.add_format({"align": "vdistributed"})
        company_id = data.get("company_id", False)
        if company_id:
            company = self.env["res.company"].browse(company_id)
        else:
            company = self.env.user.company_id
        data.update(report_model._get_report_values(data.get("partner_ids"), data))
        partners = self.env["res.partner"].browse(data.get("partner_ids"))
        sheet = workbook.add_worksheet(_("Outstanding Statement"))
        sheet.set_landscape()
        row_pos = 0
        sheet.merge_range(
            row_pos,
            0,
            row_pos,
            6,
            _("Statement of Account from %s" % (company.display_name)),
            self.format_ws_title,
        )
        row_pos += 1
        sheet.write(row_pos, 1, _("Date:"), self.format_theader_yellow_right)
        sheet.write(
            row_pos,
            2,
            fields.Date.from_string(data.get("date_end")),
            self.format_date_left,
        )
        self._size_columns(sheet)
        for partner in partners:
            invoice_address = data.get(
                "get_inv_addr", lambda x: self.env["res.partner"]
            )(partner)
            row_pos += 3
            sheet.write(
                row_pos, 1, _("Statement to:"), self.format_theader_yellow_right
            )
            sheet.merge_range(
                row_pos, 2, row_pos, 3, invoice_address.display_name, self.format_left,
            )
            if invoice_address.vat:
                sheet.write(
                    row_pos, 4, _("VAT:"), self.format_theader_yellow_right,
                )
                sheet.write(
                    row_pos, 5, invoice_address.vat, self.format_left,
                )
            row_pos += 1
            sheet.write(
                row_pos, 1, _("Statement from:"), self.format_theader_yellow_right
            )
            sheet.merge_range(
                row_pos,
                2,
                row_pos,
                3,
                company.partner_id.display_name,
                self.format_left,
            )
            if company.vat:
                sheet.write(
                    row_pos, 4, _("VAT:"), self.format_theader_yellow_right,
                )
                sheet.write(
                    row_pos, 5, company.vat, self.format_left,
                )
            partner_data = data.get("data", {}).get(partner.id)
            currencies = partner_data.get("currencies", {}).keys()
            if currencies:
                row_pos += 1
            for currency_id in currencies:
                currency = self.env["res.currency"].browse(currency_id)
                if currency.position == "after":
                    money_string = "#,##0.%s " % (
                        "0" * currency.decimal_places
                    ) + "[${}]".format(currency.symbol)
                elif currency.position == "before":
                    money_string = "[${}]".format(currency.symbol) + " #,##0.%s" % (
                        "0" * currency.decimal_places
                    )
                self.current_money_format = workbook.add_format(
                    {"align": "right", "num_format": money_string}
                )
                row_pos = self._write_currency_lines(
                    row_pos, sheet, partner, currency, data
                )
                row_pos = self._write_currency_buckets(
                    row_pos, sheet, partner, currency, data
                )
