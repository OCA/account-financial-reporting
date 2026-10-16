// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {formatDate, parseDate} from "@web/core/l10n/dates";
import {AccountReportController} from "./accountReportController.esm";
import {_t} from "@web/core/l10n/translation";
import {accountReportControllerRegistry} from "./registry.esm";

export class AgedPartnerBalanceController extends AccountReportController {
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
                key: "date_at",
                label: _t("Date at"),
                value: formatDate(parseDate(this.datas.date_at)),
            },
            {
                key: "only_posted_moves",
                label: _t("Only Posted Moves"),
                value: this.datas.only_posted_moves
                    ? _t("Posted entries")
                    : _t("All entries"),
            },
            {
                key: "show_move_lines_details",
                label: _t("Show journal items"),
                value: this.datas.show_move_lines_details ? _t("Yes") : _t("No"),
            },
        ];
    }

    _getIntervals() {
        return this.datas.age_partner_config_lines.length
            ? this.datas.age_partner_config_lines.map((line) => ({
                  key: String(line.id),
                  name: line.name,
                  percent_key: `percent_${line.id}`,
              }))
            : [
                  {
                      key: "30_days",
                      name: _t("1 - 30 d."),
                      percent_key: "percent_30_days",
                  },
                  {
                      key: "60_days",
                      name: _t("31 - 60 d."),
                      percent_key: "percent_60_days",
                  },
                  {
                      key: "90_days",
                      name: _t("61 - 90 d."),
                      percent_key: "percent_90_days",
                  },
                  {
                      key: "120_days",
                      name: _t("91 - 120 d."),
                      percent_key: "percent_120_days",
                  },
                  {key: "older", name: _t("> 120 d."), percent_key: "percent_older"},
              ];
    }

    getColumns() {
        const labels = this.datas.show_move_lines_details
            ? [
                  {key: "entry", label: _t("Entry"), show: true},
                  {key: "date", label: _t("Date"), type: "date", show: true},
                  {key: "journal", label: _t("Journal"), show: true},
                  {key: "account", label: _t("Account"), show: true},
                  {key: "ref_label", label: _t("Ref - Label"), show: true},
                  {key: "due_date", label: _t("Due date"), type: "date", show: true},
              ]
            : [{key: "partner", label: _t("Partner"), show: true}];
        return [
            ...labels,
            {key: "residual", label: _t("Residual"), type: "monetary", show: true},
            {key: "current", label: _t("Not due"), type: "monetary", show: true},
            ...this._getIntervals().map((interval) => ({
                key: interval.key,
                label: interval.name,
                type: "monetary",
                show: true,
            })),
        ];
    }

    getRows() {
        return this.datas.aged_partner_balance.map((account) => ({
            key: `account:${account.id}`,
            account: {code: account.code, name: account.name},
            ...this._getRow(account, _t("Ending balance")),
            percentages: this._getPercentages(account),
            partners: account.partners.map((partner, index) => ({
                key: `account:${account.id}:partner:${index}`,
                name: partner.name,
                ...this._getRow(partner, partner.name),
                total: this._getRow(partner, _t("Partner ending balance")),
                moveLines: (partner.move_lines || []).map((line, lineIndex) => ({
                    key: `line:${lineIndex}`,
                    ...this._getRow(line),
                })),
            })),
        }));
    }

    _getRow(data, label = "") {
        const labelKey = this.datas.show_move_lines_details ? "ref_label" : "partner";
        return {
            currencyId: this.datas.company_currency_id,
            values: this.getColumns().map((column) => ({
                key: column.key,
                value: column.key === labelKey && label ? label : data[column.key],
                clickable: false,
            })),
        };
    }

    _getPercentages(account) {
        const amounts = [
            {key: "current", percent_key: "percent_current"},
            ...this._getIntervals(),
        ];
        return {
            values: [
                {
                    key: this.datas.show_move_lines_details ? "ref_label" : "partner",
                    value: "%",
                },
                ...amounts.map((interval) => ({
                    key: interval.key,
                    value: `${account[interval.percent_key]}%`,
                })),
            ],
        };
    }

    getSidebarAccounts(rows) {
        return rows.map((row) => row.account);
    }

    extraData() {
        return {
            options: {
                reportType: "aged_partner_balance",
                filterByAccount: true,
                showMoveLineDetails: Boolean(this.datas.show_move_lines_details),
            },
            percentageColumns: this.getColumns().map((column) => ({
                ...column,
                type: undefined,
            })),
        };
    }
}

accountReportControllerRegistry.add(
    "aged_partner_balance",
    AgedPartnerBalanceController
);
