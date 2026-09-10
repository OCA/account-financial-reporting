// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {Component} from "@odoo/owl";

export class AccountReportHeader extends Component {
    static template = "account_financial_report.AccountReportHeader";

    static props = {
        env: Object,
    };

    setup() {
        super.setup();
        this.env = this.props.env;
        this.report_name = this.env.header.report_name;
        this.company_name = this.env.header.company_name;
        this.currency_name = this.env.header.currency_name;
        this.currency = this.env.header.currency;
        this.currency_model = this.env.header.currency_model;
    }
}
