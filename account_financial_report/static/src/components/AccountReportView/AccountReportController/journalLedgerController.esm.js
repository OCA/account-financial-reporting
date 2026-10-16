// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {formatDate, parseDate} from "@web/core/l10n/dates";
import {AccountReportController} from "./accountReportController.esm";
import {_t} from "@web/core/l10n/translation";
import {accountReportControllerRegistry} from "./registry.esm";

export class JournalLedgerController extends AccountReportController {
    getHeader() {
        return {
            company_name: this.datas.company_name,
            currency_name: this.datas.currency_name,
            report_name: this.params.report_name,
        };
    }

    getFilters() {
        const targets = {
            posted: _t("Posted entries"),
            draft: _t("Draft entries"),
            all: _t("All entries"),
        };
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
                key: "move_target",
                label: _t("Target Moves"),
                value: targets[this.datas.move_target],
            },
            {
                key: "group_option",
                label: _t("Group By"),
                value:
                    this.datas.group_option === "journal"
                        ? _t("Journal")
                        : _t("No grouping"),
            },
        ];
    }

    getColumns() {
        return [
            {
                key: "auto_sequence",
                label: _t("Sequence"),
                show: Boolean(this.datas.with_auto_sequence),
            },
            {key: "entry", label: _t("Entry"), show: true},
            {key: "date", label: _t("Date"), type: "date", show: true},
            {key: "account", label: _t("Account"), show: true},
            {key: "partner", label: _t("Partner"), show: true},
            {key: "label", label: _t("Ref - Label"), show: true},
            {key: "taxes", label: _t("Taxes"), type: "tags", show: true},
            {key: "debit", label: _t("Debit"), type: "monetary", show: true},
            {key: "credit", label: _t("Credit"), type: "monetary", show: true},
            {
                key: "currency",
                label: _t("Cur."),
                show: Boolean(this.datas.foreign_currency),
            },
            {
                key: "amount_currency",
                label: _t("Amount Cur."),
                type: "monetary",
                show: Boolean(this.datas.foreign_currency),
            },
        ];
    }

    getRows() {
        if (this.datas.group_option !== "journal") {
            return [
                {
                    key: "all",
                    name: _t("All entries"),
                    moves: this._getMoves(this.datas.Moves),
                    taxes: this._getTaxes(
                        this.datas.Journal_Ledgers.flatMap(
                            (journal) => journal.tax_lines
                        )
                    ),
                },
            ];
        }
        return this.datas.Journal_Ledgers.map((journal) => ({
            key: `journal:${journal.id}`,
            name: journal.name,
            moves: this._getMoves(journal.report_moves),
            taxes: this._getTaxes(journal.tax_lines),
            total: {
                currencyId: this.datas.company_currency_id,
                values: [
                    {key: "label", value: _t("Total")},
                    {key: "debit", value: journal.debit, clickable: false},
                    {key: "credit", value: journal.credit, clickable: false},
                ],
            },
        }));
    }

    getSidebarAccounts() {
        return Object.values(this.datas.account_ids_data).map((account) => ({
            code: account.code,
            name: account.name,
        }));
    }

    extraData() {
        return {
            options: {reportType: "journal_ledger", filterByAccount: false},
            taxColumns: [
                {key: "tax_name", label: _t("Name"), show: true},
                {key: "tax_code", label: _t("Description"), show: true},
                ...[
                    ["base_debit", _t("Base Debit")],
                    ["base_credit", _t("Base Credit")],
                    ["base_balance", _t("Base Balance")],
                    ["tax_debit", _t("Tax Debit")],
                    ["tax_credit", _t("Tax Credit")],
                    ["tax_balance", _t("Tax Balance")],
                ].map(([key, label]) => ({key, label, type: "monetary", show: true})),
            ],
        };
    }

    _getMoves(moves) {
        return moves.map((move) => ({
            key: `move:${move.move_id}`,
            name: move.entry,
            lines: move.report_move_lines.map((line) => {
                const account = this.datas.account_ids_data[line.account_id];
                const taxes = line.tax_line_id
                    ? [this.datas.tax_line_data[line.tax_line_id]]
                    : Object.values(
                          this.datas.move_line_ids_taxes_data[line.move_line_id] || {}
                      );
                return {
                    key: `line:${line.move_line_id}`,
                    account: {code: account.code, name: account.name},
                    currencyId: line.company_currency_id,
                    values: [
                        {key: "auto_sequence", value: line.auto_sequence},
                        {key: "entry", value: move.entry},
                        {key: "date", value: line.date},
                        {
                            key: "account",
                            value: this.datas.with_account_name
                                ? `${account.code} - ${account.name}`
                                : account.code,
                        },
                        {
                            key: "partner",
                            value:
                                this.datas.partner_ids_data[line.partner_id]?.name ||
                                "",
                        },
                        {key: "label", value: line.label || "/"},
                        {
                            key: "taxes",
                            value: taxes
                                .filter(Boolean)
                                .map((tax) => tax.description || tax.name)
                                .filter(Boolean),
                        },
                        {key: "debit", value: line.debit, clickable: false},
                        {key: "credit", value: line.credit, clickable: false},
                        {
                            key: "currency",
                            value:
                                this.datas.currency_ids_data[line.currency_id]?.name ||
                                "",
                        },
                        {
                            key: "amount_currency",
                            value: line.amount_currency,
                            currencyId: line.currency_id,
                            clickable: false,
                        },
                    ],
                };
            }),
        }));
    }

    _getTaxes(taxes) {
        return taxes.map((tax, index) => ({
            key: `tax:${index}`,
            currencyId: this.datas.company_currency_id,
            values: Object.entries(tax).map(([key, value]) => ({
                key,
                value,
                clickable: false,
            })),
        }));
    }
}

accountReportControllerRegistry.add("journal_ledger", JournalLedgerController);
