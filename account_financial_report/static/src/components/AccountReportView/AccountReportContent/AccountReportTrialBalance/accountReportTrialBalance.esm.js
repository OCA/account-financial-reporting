// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {AccountReportLines} from "../AccountReportLines/accountReportLines.esm";
import {Component} from "@odoo/owl";

export class AccountReportTrialBalance extends Component {
    static template = "account_financial_report.AccountReportTrialBalance";

    static props = {
        env: Object,
    };

    static components = {
        AccountReportLines,
    };

    /**
     * Build pagination units without splitting a hierarchy group across pages.
     * Flat reports and partner details keep one source row per pagination unit.
     * Hierarchy sections contain a heading row and its ordered descendants;
     * amounts are preserved from the backend rather than recalculated.
     *
     * @param {Object[]} rows Account rows after applying the sidebar filter.
     * @param {Object} options Report display options.
     * @returns {Object[]} Source rows or sections shaped as {key, group, rows}.
     */
    static getPaginationItems(rows, options) {
        if (!options.showHierarchy || options.showPartnerDetails) {
            return rows;
        }
        const groups = rows.filter((row) => row.type === "group_type");
        // Compare full path segments so that "1" is not an ancestor of "10".
        const path = (row) =>
            (row.completeCode || "")
                .split("/")
                .map((part) => part.trim())
                .filter(Boolean);
        // Filtering may remove ancestors: use the highest groups still available.
        const roots = groups.filter(
            (group) =>
                !groups.some(
                    (parent) =>
                        parent !== group &&
                        path(parent).length < path(group).length &&
                        path(parent).every((part, index) => path(group)[index] === part)
                )
        );
        const sections = roots.map((group) => ({
            key: group.key,
            group,
            rows: [],
        }));
        for (const row of rows) {
            const section = sections.find(
                ({group}) =>
                    group.type === "group_type" &&
                    path(group).length &&
                    path(group).every((part, index) => path(row)[index] === part)
            );
            if (section) {
                // The root already supplies the section heading and total row.
                if (row !== section.group) {
                    section.rows.push(row);
                }
            } else {
                // Keep ungrouped accounts and rows with missing paths visible.
                sections.push({key: row.key, group: row, rows: []});
            }
        }
        return sections;
    }

    setup() {
        super.setup();
        this.env = this.props.env;
    }

    /** Return the current page of sections when hierarchy mode is active. */
    get reportSections() {
        return this.env.filteredRows;
    }

    /** Expose the current page as rows, flattening hierarchy sections if needed. */
    get getRows() {
        if (this.options.showHierarchy && !this.options.showPartnerDetails) {
            return this.reportSections.flatMap((section) => [
                section.group,
                ...section.rows,
            ]);
        }
        return this.env.filteredRows;
    }

    get getColumns() {
        return this.env.columns;
    }

    get options() {
        return this.env.options;
    }
}
