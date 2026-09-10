// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {Component, onWillStart, useState} from "@odoo/owl";
import {formatDate, parseDate} from "@web/core/l10n/dates";
import {Pager} from "@web/core/pager/pager";
import {formatMonetary} from "@web/views/fields/formatters";
import {useService} from "@web/core/utils/hooks";

export class AccountReportMoveLines extends Component {
    static template = "account_financial_report.AccountReportMoveLines";
    static components = {
        Pager,
    };
    static props = {
        row: Object,
        key: String,
        title: {
            type: String,
            optional: true,
        },
    };

    get title() {
        return this.props.title || "";
    }

    get currencyId() {
        return this.props.row.currencyId || null;
    }

    get totalDebit() {
        return Math.sumPrecise(this.records.map((record) => record.debit));
    }

    get totalCredit() {
        return Math.sumPrecise(this.records.map((record) => record.credit));
    }

    get totalRecords() {
        return this.records.length;
    }

    get filteredRecords() {
        const {offset, limit} = this.state.pagination;
        return this.records.slice(offset, offset + limit);
    }

    get pagination() {
        return this.state.pagination;
    }

    get records() {
        return this.state.records;
    }

    set records(value) {
        this.state.records = value;
    }

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.ui = useService("ui");
        this.state = useState({
            records: [],
            pagination: {offset: 0, limit: 10},
        });
        onWillStart(async () => {
            await this._load_data();
        });
    }

    async _load_data() {
        this.ui.block();
        try {
            this.records = await this.orm.searchRead(
                "account.move.line",
                this._loadDataDomain(),
                this._loadDataFields()
            );
        } finally {
            this.ui.unblock();
        }
    }

    _loadDataDomain() {
        return (
            this.props.row.values.filter((value) => value.key === this.props.key)[0]
                .domain || []
        );
    }

    _loadDataFields() {
        return ["id", "date", "name", "debit", "credit", "journal_id", "account_id"];
    }

    formatMonetary(value, currencyId) {
        return formatMonetary(value, {currencyId: currencyId});
    }

    formatDate(value) {
        return formatDate(parseDate(value));
    }

    onPagerUpdate({offset, limit}) {
        this.state.pagination = {offset, limit};
    }
}
