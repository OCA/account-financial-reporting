// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {Component, useState} from "@odoo/owl";
import {AccountReportLines} from "../AccountReportLines/accountReportLines.esm";
import {_t} from "@web/core/l10n/translation";

export class AccountReportGeneralLedger extends Component {
    static template = "account_financial_report.AccountReportGeneralLedger";
    static props = {env: Object};
    static components = {AccountReportLines};

    setup() {
        this.state = useState({collapsedGroups: {}});
    }

    isGroupOpen(group) {
        return !this.state.collapsedGroups[group.key];
    }

    toggleGroup(group) {
        this.state.collapsedGroups[group.key] = this.isGroupOpen(group);
    }

    get rows() {
        return this.props.env.filteredRows;
    }

    get columns() {
        return this.props.env.columns.filter((column) => column.show);
    }

    get groupLabelColspan() {
        return this.columns.findIndex((column) => column.key === "ref_label");
    }

    get groupBalanceColumns() {
        return this.columns.slice(this.groupLabelColspan);
    }

    balanceRow(section, account, initial = false) {
        let label = null;
        if (section !== account && account.groupedBy === "partners") {
            label = initial
                ? _t("Partner initial balance")
                : _t("Partner ending balance");
        } else if (section !== account && account.groupedBy === "taxes") {
            label = initial ? _t("Tax initial balance") : _t("Tax ending balance");
        } else {
            label = initial ? _t("Initial balance") : _t("Ending balance");
        }
        return {
            currencyId: account.currencyId,
            values: [
                {key: "ref_label", value: label},
                ...(initial ? section.initialValues : section.values),
            ],
        };
    }
}
