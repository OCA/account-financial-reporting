// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {formatDate, parseDate} from "@web/core/l10n/dates";
import {AccountReportController} from "./accountReportController.esm";
import {_t} from "@web/core/l10n/translation";
import {accountReportControllerRegistry} from "./registry.esm";

export class GeneralLedgerController extends AccountReportController {
    getHeader() {
        return {
            company_name: this.datas.company_name,
            company_currency: this.datas.company_currency,
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
                key: "only_posted_moves",
                label: _t("Only Posted Moves"),
                value: this.datas.only_posted_moves
                    ? _t("Posted entries")
                    : _t("All entries"),
            },
            {
                key: "hide_account_at_0",
                label: _t("Account at 0"),
                value: this.datas.hide_account_at_0 ? _t("Hide") : _t("Show"),
            },
            {
                key: "centralize",
                label: _t("Centralize"),
                value: this.datas.centralize ? _t("Yes") : _t("No"),
            },
        ];
    }

    getColumns() {
        return [
            {key: "date", label: _t("Date"), type: "date", show: true},
            {key: "entry", label: _t("Entry"), show: true},
            {key: "journal", label: _t("Journal"), show: true},
            {key: "account", label: _t("Account"), show: true},
            {key: "taxes", label: _t("Taxes"), show: true},
            {key: "partner", label: _t("Partner"), show: true},
            {key: "ref_label", label: _t("Ref - Label"), show: true},
            {
                key: "analytic_distribution",
                label: _t("Analytic Distribution"),
                show: Boolean(this.datas.show_cost_center),
            },
            {key: "reconciliation", label: _t("Rec."), show: true},
            {key: "debit", label: _t("Debit"), type: "monetary", show: true},
            {key: "credit", label: _t("Credit"), type: "monetary", show: true},
            {key: "balance", label: _t("Cumul. Bal."), type: "monetary", show: true},
            {
                key: "amount_currency",
                label: _t("Amount cur."),
                type: "monetary",
                show: Boolean(this.datas.foreign_currency),
            },
            {
                key: "cumulative_currency",
                label: _t("Cumul cur."),
                type: "monetary",
                show: Boolean(this.datas.foreign_currency),
            },
        ];
    }

    getRows() {
        return this.datas.general_ledger.map((account) => {
            const row = {
                key: `account:${account.id}`,
                id: account.id,
                account: {code: account.code, name: account.name},
                currencyId: this._currencyId(this.datas.company_currency),
                includeInitialBalance: account.include_initial_balance,
                groupedBy: account.grouped_by || this.params.data?.grouped_by || "none",
                showTotal: !account.list_grouped || !this.datas.filter_partner_ids,
                ...this._getSection(account, account),
            };
            if (Object.hasOwn(account, "list_grouped")) {
                row.groups = account.list_grouped.map((group) => ({
                    key: `${row.key}:group:${group.id}`,
                    id: group.id,
                    name: group.name,
                    ...this._getSection(group, account),
                }));
            }
            return row;
        });
    }

    extraData() {
        return {
            options: {
                reportType: "general_ledger",
                filterByAccount: true,
                foreignCurrency: Boolean(this.datas.foreign_currency),
                showCostCenter: Boolean(this.datas.show_cost_center),
                groupedBy: this.params.data?.grouped_by || "none",
            },
        };
    }

    _currencyId(currency) {
        if (Array.isArray(currency)) return currency[0] || null;
        if (typeof currency === "number") return currency || null;
        const match = typeof currency === "string" && currency.match(/\((\d+),\)/);
        return match ? Number(match[1]) : null;
    }

    _getSection(section, account) {
        const companyCurrencyId = this._currencyId(this.datas.company_currency);
        let cumulativeCurrency = section.init_bal.bal_curr || 0;
        return {
            initialValues: this._getBalanceValues(
                section.init_bal,
                account.currency_id
            ),
            values: this._getBalanceValues(
                section.fin_bal,
                account.fin_bal_currency_id
            ),
            moveLines: (section.move_lines || []).map((line, index) => {
                const currencyId = this._currencyId(line.currency_id);
                const foreignCurrency = currencyId && currencyId !== companyCurrencyId;
                if (foreignCurrency) cumulativeCurrency += line.bal_curr;
                return {
                    key: `line:${line.id || "centralized"}:${index}`,
                    id: line.id,
                    currencyId: companyCurrencyId,
                    values: [
                        {key: "date", value: line.date},
                        {key: "entry", value: line.entry},
                        {
                            key: "journal",
                            value:
                                this.datas.journals_data[line.journal_id]?.code || "",
                        },
                        {
                            key: "account",
                            value:
                                this.datas.accounts_data[line.account_id]?.code ||
                                account.code,
                        },
                        {
                            key: "taxes",
                            value: (line.tax_ids || [])
                                .map((id) => this.datas.taxes_data[id]?.tax_name || "")
                                .filter(Boolean)
                                .join(", "),
                        },
                        {key: "partner", value: line.partner_name || ""},
                        {key: "ref_label", value: line.ref_label || ""},
                        {
                            key: "analytic_distribution",
                            value: this._getAnalyticDistribution(line),
                        },
                        {key: "reconciliation", value: line.rec_name || ""},
                        ...["debit", "credit", "balance"].map((key) => ({
                            key,
                            value: line[key],
                            domain: line.id ? [["id", "=", line.id]] : [],
                            clickable: false,
                        })),
                        {
                            key: "amount_currency",
                            value: foreignCurrency ? line.bal_curr : null,
                            currencyId,
                        },
                        {
                            key: "cumulative_currency",
                            value: foreignCurrency ? cumulativeCurrency : null,
                            currencyId,
                        },
                    ],
                };
            }),
        };
    }

    _getBalanceValues(balance, currency) {
        const currencyId = this._currencyId(currency);
        return [
            ...["debit", "credit", "balance"].map((key) => ({
                key,
                value: balance[key],
            })),
            {
                key: "amount_currency",
                value: currencyId ? balance.bal_curr : null,
                currencyId,
            },
            {
                key: "cumulative_currency",
                value: currencyId ? balance.bal_curr : null,
                currencyId,
            },
        ];
    }

    _getAnalyticDistribution(line) {
        return Object.entries(line.analytic_distribution || {})
            .map(([ids, percentage]) => {
                const names = ids
                    .split(",")
                    .map((id) => this.datas.analytic_data[id]?.name || id);
                return `${names.join(", ")}: ${percentage}%`;
            })
            .join("; ");
    }
}

accountReportControllerRegistry.add("general_ledger", GeneralLedgerController);
