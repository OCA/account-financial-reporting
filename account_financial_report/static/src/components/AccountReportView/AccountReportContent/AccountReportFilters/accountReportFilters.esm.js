// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {Component, useState} from "@odoo/owl";

export class AccountReportFilters extends Component {
    static template = "account_financial_report.AccountReportFilters";

    static props = {
        env: Object,
    };

    setup() {
        super.setup();
        this.env = this.props.env;
        this.state = useState({open: true});
    }

    toggleFilters() {
        this.state.open = !this.state.open;
    }

    get filters() {
        return this.env.filters;
    }
}
