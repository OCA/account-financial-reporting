// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {Component, useState} from "@odoo/owl";
import {AccountReportLines} from "../AccountReportLines/accountReportLines.esm";

export class AccountReportAgedPartnerBalance extends Component {
    static template = "account_financial_report.AccountReportAgedPartnerBalance";
    static props = {env: Object};
    static components = {AccountReportLines};

    setup() {
        this.state = useState({collapsedPartners: {}});
    }

    get rows() {
        return this.props.env.filteredRows;
    }
    get columns() {
        return this.props.env.columns;
    }
    get options() {
        return this.props.env.options;
    }
    get percentageColumns() {
        return this.props.env.percentageColumns;
    }
    get partnerLabelColspan() {
        return this.columns.findIndex((column) => column.key === "ref_label");
    }
    get partnerBalanceColumns() {
        return this.columns.slice(this.partnerLabelColspan);
    }

    isPartnerOpen(partner) {
        return !this.state.collapsedPartners[partner.key];
    }
    togglePartner(partner) {
        this.state.collapsedPartners[partner.key] = this.isPartnerOpen(partner);
    }
}
