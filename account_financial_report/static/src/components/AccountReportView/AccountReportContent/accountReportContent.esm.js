// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {AccountReportFilters} from "./AccountReportFilters/accountReportFilters.esm";
import {AccountReportSidebar} from "./AccountReportSidebar/accountReportSidebar.esm";
import {AccountReportTrialBalance} from "./AccountReportTrialBalance/accountReportTrialBalance.esm";
import {Component} from "@odoo/owl";
import {Pager} from "@web/core/pager/pager";

export class AccountReportContent extends Component {
    static template = "account_financial_report.AccountReportContent";

    static components = {
        AccountReportFilters,
        AccountReportTrialBalance,
        AccountReportSidebar,
        Pager,
    };

    static props = {
        env: Object,
    };

    components_map = {
        trial_balance: AccountReportTrialBalance,
    };

    setup() {
        super.setup();
        this.env = this.props.env;
        this.env.sidebarOpen = false;
        this.env.selectedAccountPrefix = "";
        this.env.filteredRows = [];
        this.updateFilteredRows();
    }

    get filterByAccount() {
        return this.env.options.filterByAccount;
    }

    get sidebarOpen() {
        return this.env.sidebarOpen;
    }

    get pagination() {
        return this.env.pagination;
    }

    /** Count pagination units, which may be whole sections rather than rows. */
    get totalRows() {
        return this.paginationItems.length;
    }

    /** Apply the account prefix filter before report-specific grouping. */
    get accountRows() {
        const prefix = this.env.selectedAccountPrefix;
        if (!prefix) {
            return this.env.rows;
        }
        return this.env.rows.filter((row) => {
            const code =
                row.account?.code ??
                row.values.find((value) => value.key === "code")?.value;
            return (
                code !== undefined &&
                code !== null &&
                String(code).trim().startsWith(prefix)
            );
        });
    }

    /**
     * Let each report component prepare its own pagination units.
     * Components without this optional static hook paginate source rows directly.
     */
    get paginationItems() {
        const rows = this.accountRows;
        return this.component?.getPaginationItems
            ? this.component.getPaginationItems(rows, this.env.options)
            : rows;
    }

    /**
     * Apply a sidebar selection and reset the page to avoid a stale offset.
     * @param {String} prefix Account prefix; an empty string clears the filter.
     */
    onAccountPrefixSelect(prefix) {
        this.env.selectedAccountPrefix = prefix;
        this.pagination.offset = 0;
        this.updateFilteredRows();
    }

    get component() {
        return this.components_map[this.env.options.reportType];
    }

    toggleSidebar() {
        this.env.sidebarOpen = !this.env.sidebarOpen;
    }

    /** Store the current page; the report component interprets its item shape. */
    updateFilteredRows() {
        const {offset, limit} = this.pagination;
        this.env.filteredRows = this.paginationItems.slice(offset, offset + limit);
    }

    onPagerUpdate({offset, limit}) {
        this.env.pagination.offset = offset;
        this.env.pagination.limit = limit;
        this.updateFilteredRows();
    }
}
