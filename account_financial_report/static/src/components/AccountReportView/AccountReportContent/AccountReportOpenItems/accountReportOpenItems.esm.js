// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {AccountReportLines} from "../AccountReportLines/accountReportLines.esm";
import {Component} from "@odoo/owl";

export class AccountReportOpenItems extends Component {
    static template = "account_financial_report.AccountReportOpenItems";
    static props = {env: Object};
    static components = {AccountReportLines};

    get rows() {
        return this.props.env.filteredRows;
    }
    get columns() {
        return this.props.env.columns;
    }
}
