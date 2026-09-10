// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {Component, useState} from "@odoo/owl";

export class AccountReportSidebar extends Component {
    static template = "account_financial_report.AccountReportSidebar";

    static props = {
        env: Object,
        onSelect: Function,
    };

    setup() {
        this.state = useState({expanded: {}, search: ""});
    }

    get searchQuery() {
        return this.normalizeSearch(this.state.search.trim());
    }

    normalizeSearch(value) {
        return String(value)
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase();
    }

    togglePrefix(prefix) {
        this.state.expanded[prefix] = !this.state.expanded[prefix];
    }

    get visiblePrefixes() {
        const prefixes = this.prefixes;
        const accounts = this.accounts;
        const parents = new Set(prefixes.map((prefix) => prefix.slice(0, -1)));
        return prefixes
            .filter((prefix) => {
                if (this.searchQuery) {
                    return true;
                }
                for (let length = 1; length < prefix.length; length++) {
                    if (!this.state.expanded[prefix.slice(0, length)]) {
                        return false;
                    }
                }
                return true;
            })
            .map((prefix) => ({
                code: prefix,
                name: accounts.get(prefix) || "",
                hasChildren: parents.has(prefix),
                expanded: Boolean(this.state.expanded[prefix]),
            }));
    }

    get accounts() {
        const accounts = new Map();
        for (const row of this.props.env.rows) {
            const code =
                row.account?.code ??
                row.values.find((value) => value.key === "code")?.value;
            if (code === undefined || code === null || code === false) {
                continue;
            }
            const accountCode = String(code).trim();
            if (!accountCode) {
                continue;
            }
            const name =
                row.account?.name ??
                row.values.find((value) => value.key === "account")?.value;
            accounts.set(accountCode, name || "");
        }
        return accounts;
    }

    get prefixes() {
        const prefixes = new Set();
        const query = this.searchQuery;
        for (const [accountCode, name] of this.accounts) {
            if (
                query &&
                !this.normalizeSearch(accountCode).includes(query) &&
                !this.normalizeSearch(name).includes(query)
            ) {
                continue;
            }
            for (let length = 1; length <= accountCode.length; length++) {
                prefixes.add(accountCode.slice(0, length));
            }
        }
        return [...prefixes].sort();
    }
}
