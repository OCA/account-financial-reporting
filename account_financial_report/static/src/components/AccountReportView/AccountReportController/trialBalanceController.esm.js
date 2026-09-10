// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {formatDate, parseDate} from "@web/core/l10n/dates";
import {AccountReportController} from "./accountReportController.esm";
import {_t} from "@web/core/l10n/translation";
import {accountReportControllerRegistry} from "./registry.esm";

export class TrialBalanceController extends AccountReportController {
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
                key: "hide_account_at_0",
                label: _t("Account at 0"),
                value: this.datas.hide_account_at_0 ? _t("Hide") : _t("Show"),
            },
            {
                key: "only_posted_moves",
                label: _t("Only Posted Moves"),
                value: this.datas.only_posted_moves
                    ? _t("Posted entries")
                    : _t("All entries"),
            },
            {
                key: "limit_hierarchy_level",
                label: _t("Limit hierarchy levels"),
                value: this.datas.limit_hierarchy_level
                    ? _t("Level %s", this.datas.show_hierarchy_level)
                    : _t("No limit"),
            },
        ];
    }
    getColumns() {
        const showPartnerDetails = this.datas.show_partner_details;
        if (!showPartnerDetails) return this._getTrialBalancesColumns();
        return this._getShowPartnerDetailsColumns();
    }

    getRows() {
        const showPartnerDetails = this.datas.show_partner_details;
        if (!showPartnerDetails) return this._getTrialBalances();
        return this._getShowPartnerDetails();
    }

    extraData() {
        const res = super.extraData();
        Object.assign(res, {
            options: this._getOptions(),
        });
        return res;
    }

    _getCurrency() {
        const match = this.datas.company_currency.match(/\((\d+),\)/);
        const currencyId = match ? Number(match[1]) : null;
        return currencyId;
    }

    _getTrialBalancesColumns() {
        return [
            {
                key: "code",
                label: _t("Code"),
                show: true,
            },
            {
                key: "account",
                label: _t("Account"),
                show: true,
            },
            ...this._getCommonColumns(),
        ];
    }

    _getShowPartnerDetailsColumns() {
        return [
            {
                key: "partner",
                label: _t("Partner"),
                show: true,
            },
            ...this._getCommonColumns(),
        ];
    }

    _getTrialBalances() {
        const array = [];
        const currencyId = this._getCurrency();
        for (const trialBalance of this.datas.trial_balance) {
            const id = trialBalance.id;
            const hierarchy = this.datas.show_hierarchy
                ? {
                      level: trialBalance.level,
                      parentId: trialBalance.parent_id,
                      type: trialBalance.type,
                      completeCode: trialBalance.complete_code,
                  }
                : {};
            array.push({
                ...hierarchy,
                key: `${trialBalance.type || "account_type"}:${id}`,
                id: id,
                currencyId: trialBalance.currency_id
                    ? trialBalance.currency_id
                    : currencyId,
                values: [
                    {
                        key: "code",
                        value: trialBalance.code,
                    },
                    {
                        key: "account",
                        value: trialBalance.name,
                    },
                    ...(trialBalance.type === "group_type"
                        ? this._getTotalValues(trialBalance)
                        : this._getCommonRows(trialBalance, id)),
                ],
            });
        }
        return array;
    }

    _getShowPartnerDetails() {
        const array = [];
        const currencyId = this._getCurrency();
        for (const amount of Object.entries(this.datas.total_amount)) {
            var account = this.datas.accounts_data[amount[0]];
            const partners = [];
            const partnerIds = Object.keys(this.datas.partners_data);
            for (const id of partnerIds) {
                if (!amount[1][id]) continue;
                var partnerData = amount[1][id];
                partners.push({
                    id: parseInt(id, 10),
                    currencyId: partnerData.currency_id
                        ? partnerData.currency_id
                        : currencyId,
                    values: [
                        {
                            key: "partner",
                            value: partnerData.partner_name,
                        },
                        ...this._getCommonRows(
                            partnerData,
                            parseInt(amount[0], 10),
                            parseInt(id, 10)
                        ),
                    ],
                });
            }
            array.push({
                id: parseInt(amount[0], 10),
                currencyId: account.currency_id ? account.currency_id : currencyId,
                account: {
                    code: account.code,
                    name: account.name,
                },
                partners: partners,
                values: this._getTotalValues(amount[1]),
            });
        }
        return array;
    }

    _getOptions() {
        return {
            showPartnerDetails: this.datas.show_partner_details,
            reportType: this.params.report_type,
            filterByAccount: true,
            showHierarchy: Boolean(this.datas.show_hierarchy),
            showHierarchyLevel: this.datas.show_hierarchy_level,
        };
    }

    _getCommonColumns() {
        return [
            {
                key: "initial_balance",
                label: _t("Initial balance"),
                show: true,
                type: "monetary",
            },
            {
                key: "debit",
                label: _t("Debit"),
                show: true,
                type: "monetary",
            },
            {
                key: "credit",
                label: _t("Credit"),
                show: true,
                type: "monetary",
            },
            {
                key: "period_balance",
                label: _t("Period Balance"),
                show: true,
                type: "monetary",
            },
            {
                key: "ending_balance",
                label: _t("Ending Balance"),
                show: true,
                type: "monetary",
            },
            {
                key: "initial_currency_balance",
                label: _t("Initial Curr Balance"),
                show: this.datas.foreign_currency,
                type: "monetary",
            },
            {
                key: "ending_currency_balance",
                label: _t("Ending Curr Balance"),
                show: this.datas.foreign_currency,
                type: "monetary",
            },
        ];
    }

    _getCommonRows(data, accountId = null, partnerId = null) {
        return [
            {
                key: "initial_balance",
                value: data.initial_balance,
                domain: this._domain("initial_balance", accountId, partnerId),
                clickable: data.initial_balance !== 0.0,
            },
            {
                key: "debit",
                value: data.debit,
                domain: this._domain("debit", accountId, partnerId),
                clickable: data.debit !== 0.0,
            },
            {
                key: "credit",
                value: data.credit,
                domain: this._domain("credit", accountId, partnerId),
                clickable: data.credit !== 0.0,
            },
            {
                key: "period_balance",
                value: data.balance,
                domain: this._domain("period_balance", accountId, partnerId),
                clickable: data.balance !== 0.0,
            },
            {
                key: "ending_balance",
                value: data.ending_balance,
                domain: this._domain("ending_balance", accountId, partnerId),
                clickable: data.ending_balance !== 0.0,
            },
            {
                key: "initial_currency_balance",
                value: data.initial_currency_balance,
                domain: this._domain("initial_currency_balance", accountId, partnerId),
                clickable: data.initial_currency_balance !== 0.0,
            },
            {
                key: "ending_currency_balance",
                value: data.ending_currency_balance,
                domain: this._domain("ending_currency_balance", accountId, partnerId),
                clickable: data.ending_currency_balance !== 0.0,
            },
        ];
    }

    _getTotalValues(data) {
        return [
            {
                key: "initial_balance",
                value: data.initial_balance,
            },
            {
                key: "debit",
                value: data.debit,
            },
            {
                key: "credit",
                value: data.credit,
            },
            {
                key: "period_balance",
                value: data.balance,
            },
            {
                key: "ending_balance",
                value: data.ending_balance,
            },
            {
                key: "initial_currency_balance",
                value: data.initial_currency_balance,
            },
            {
                key: "ending_currency_balance",
                value: data.ending_currency_balance,
            },
        ];
    }

    _domain(key, accountId = null, partnerId = null) {
        const periodDomain = [
            ["date", ">=", this.datas.date_from],
            ["date", "<=", this.datas.date_to],
        ];
        const parentDomain = this.datas.only_posted_moves
            ? [["parent_state", "=", "posted"]]
            : [["parent_state", "in", ["posted", "draft"]]];
        const commonDomain = [...parentDomain, ["account_id", "=", accountId]];
        const partnerDomain = this.datas.show_partner_details
            ? [["partner_id", "=", partnerId]]
            : [];
        const domainsByKey = {
            initial_balance: [["date", "<", this.datas.date_from]],
            debit: [...periodDomain, ["debit", "<>", 0]],
            credit: [...periodDomain, ["credit", "<>", 0]],
            period_balance: [...periodDomain, ["balance", "<>", 0]],
            ending_balance: [["date", "<=", this.datas.date_to]],
            initial_currency_balance: [],
            ending_currency_balance: [],
        };
        return [...domainsByKey[key], ...commonDomain, ...partnerDomain];
    }
}

accountReportControllerRegistry.add("trial_balance", TrialBalanceController);
