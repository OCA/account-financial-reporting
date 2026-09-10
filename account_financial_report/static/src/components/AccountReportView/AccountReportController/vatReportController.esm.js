// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {formatDate, parseDate} from "@web/core/l10n/dates";
import {AccountReportController} from "./accountReportController.esm";
import {_t} from "@web/core/l10n/translation";
import {accountReportControllerRegistry} from "./registry.esm";

export class VATReportController extends AccountReportController {
    getHeader() {
        return {
            company_name: this.datas.company_name,
            currency_name: this.datas.currency_name,
            report_name: this.params.report_name,
        };
    }

    getFilters() {
        return [
            {
                key: "date_range",
                label: _t("Date Range"),
                value: _t(
                    "From: %s To: %s",
                    formatDate(parseDate(this.datas.date_from)),
                    formatDate(parseDate(this.datas.date_to))
                ),
            },
            {
                key: "based_on",
                label: _t("Based On"),
                value:
                    this.datas.based_on === "taxgroups"
                        ? _t("Tax Groups")
                        : _t("Tax Tags"),
            },
            {
                key: "tax_detail",
                label: _t("Detail Taxes"),
                value: this.datas.tax_detail ? _t("Yes") : _t("No"),
            },
            {
                key: "only_posted_moves",
                label: _t("Only Posted Moves"),
                value: this.params.data.only_posted_moves
                    ? _t("Posted entries")
                    : _t("All entries"),
            },
        ];
    }

    getColumns() {
        return [
            {key: "code", label: _t("Code"), show: true},
            {key: "name", label: _t("Name"), show: true},
            {key: "net", label: _t("Net"), type: "monetary", show: true},
            {key: "tax", label: _t("Tax"), type: "monetary", show: true},
        ];
    }

    getRows() {
        return this.datas.vat_report.map((group, index) => ({
            key: `group:${index}`,
            ...this._getRow(group),
            taxes: this.datas.tax_detail
                ? (group.taxes || []).map((tax) => ({
                      key: `group:${index}:tax:${tax.id}`,
                      ...this._getRow(tax, true),
                  }))
                : [],
        }));
    }

    _getRow(data, detail = false) {
        return {
            currencyId: this.datas.company_currency_id,
            values: this.getColumns().map((column) => {
                const cell = {key: column.key, value: data[column.key]};
                if (detail && ["net", "tax"].includes(column.key)) {
                    cell.clickable = true;
                    cell.domain = [
                        ...(this.datas.move_line_domain || []),
                        column.key === "net"
                            ? ["tax_ids", "in", [data.id]]
                            : ["tax_line_id", "=", data.id],
                    ];
                }
                return cell;
            }),
        };
    }

    extraData() {
        return {options: {reportType: "vat_report", filterByAccount: false}};
    }
}

accountReportControllerRegistry.add("vat_report", VATReportController);
