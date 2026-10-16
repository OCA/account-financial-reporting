// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {formatDate, parseDate} from "@web/core/l10n/dates";
import {AccountReportController} from "./accountReportController.esm";
import {_t} from "@web/core/l10n/translation";
import {accountReportControllerRegistry} from "./registry.esm";

export class OpenItemsController extends AccountReportController {
    getHeader() {
        return {
            company_name: this.datas.company_name,
            currency_name: this.datas.currency_name,
            report_name: this.params.report_name,
        };
    }

    getFilters() {
        const filters = [
            {
                key: "date_at",
                label: _t("Date at"),
                value: formatDate(parseDate(this.params.data.date_at)),
            },
            {
                key: "only_posted_moves",
                label: _t("Only Posted Moves"),
                value: this.params.data.only_posted_moves
                    ? _t("Posted entries")
                    : _t("All entries"),
            },
            {
                key: "hide_account_at_0",
                label: _t("Account at 0"),
                value: this.datas.hide_account_at_0 ? _t("Hide") : _t("Show"),
            },
            {
                key: "show_partner_details",
                label: _t("Show partner details"),
                value: this.datas.show_partner_details ? _t("Yes") : _t("No"),
            },
            {
                key: "grouped_by",
                label: _t("Grouped by"),
                value:
                    this.datas.grouped_by === "salesperson"
                        ? _t("Partner Salesperson")
                        : _t("Partners"),
            },
        ];
        if (this.params.data.date_from) {
            filters.unshift({
                key: "date_from",
                label: _t("Date from"),
                value: formatDate(parseDate(this.params.data.date_from)),
            });
        }
        return filters;
    }

    getColumns() {
        return [
            {key: "date", label: _t("Date"), type: "date"},
            {key: "move_name", label: _t("Entry")},
            {key: "journal", label: _t("Journal")},
            {key: "account", label: _t("Account")},
            {key: "partner_name", label: _t("Partner")},
            {key: "ref_label", label: _t("Ref - Label")},
            {key: "date_maturity", label: _t("Due date")},
            {key: "original", label: _t("Original"), type: "monetary"},
            {key: "amount_residual", label: _t("Residual"), type: "monetary"},
            ...(this.datas.foreign_currency
                ? [
                      {key: "currency_name", label: _t("Currency")},
                      {
                          key: "amount_currency",
                          label: _t("Amount cur."),
                          type: "monetary",
                      },
                      {
                          key: "amount_residual_currency",
                          label: _t("Residual cur."),
                          type: "monetary",
                      },
                  ]
                : []),
        ].map((column) => ({...column, show: true}));
    }

    _getRow(line, account) {
        return {
            key: `line:${line.id}`,
            currencyId: this.datas.company_currency_id,
            values: this.getColumns().map((column) => ({
                key: column.key,
                value:
                    column.key === "journal"
                        ? this.datas.journals_data[line.journal_id]?.code
                        : column.key === "account"
                          ? account.code
                          : line[column.key],
                ...(["amount_currency", "amount_residual_currency"].includes(column.key)
                    ? {
                          currencyId: line.currency_id,
                          value: line.currency_id ? line[column.key] : null,
                      }
                    : {}),
            })),
        };
    }

    _getTotal(residual, label) {
        return {
            currencyId: this.datas.company_currency_id,
            values: [
                {key: "ref_label", value: label},
                {key: "amount_residual", value: residual},
            ],
        };
    }

    getRows() {
        return Object.entries(this.datas.Open_Items)
            .map(([id, items]) => {
                const account = this.datas.accounts_data[id];
                const total = this.datas.total_amount[id];
                const row = {
                    key: `account:${id}`,
                    account: {code: account.code, name: account.name},
                    total: this._getTotal(total.residual, _t("Ending balance")),
                    groups: [],
                    moveLines: [],
                };
                if (Array.isArray(items)) {
                    row.moveLines = items.map((line) => this._getRow(line, account));
                } else {
                    row.groups = Object.entries(items)
                        .map(([groupId, lines]) => ({
                            key: `${row.key}:group:${groupId}`,
                            name:
                                this.datas.partners_data[groupId]?.name ||
                                _t("Missing Partner"),
                            total: this._getTotal(
                                total[groupId].residual,
                                _t("Partner ending balance")
                            ),
                            moveLines: lines.map((line) => this._getRow(line, account)),
                            partners:
                                this.datas.grouped_by === "salesperson"
                                    ? Array.from(
                                          new Set(lines.map((line) => line.partner_id))
                                      ).map((partnerId) => {
                                          const partnerLines = lines.filter(
                                              (line) => line.partner_id === partnerId
                                          );
                                          return {
                                              key: `${row.key}:group:${groupId}:partner:${partnerId}`,
                                              name:
                                                  partnerLines[0].partner_name ||
                                                  _t("Missing Partner"),
                                              moveLines: partnerLines.map((line) =>
                                                  this._getRow(line, account)
                                              ),
                                              total: this._getTotal(
                                                  partnerLines.reduce(
                                                      (sum, line) =>
                                                          sum + line.amount_residual,
                                                      0
                                                  ),
                                                  _t("Partner ending balance")
                                              ),
                                          };
                                      })
                                    : [],
                        }))
                        .sort((a, b) => a.name.localeCompare(b.name));
                }
                return row;
            })
            .sort((a, b) => a.account.code.localeCompare(b.account.code));
    }

    getSidebarAccounts(rows) {
        return rows.map((row) => row.account);
    }

    extraData() {
        return {options: {reportType: "open_items", filterByAccount: true}};
    }
}

accountReportControllerRegistry.add("open_items", OpenItemsController);
