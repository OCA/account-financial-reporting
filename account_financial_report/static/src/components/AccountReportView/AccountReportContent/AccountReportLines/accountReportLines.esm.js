// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {AccountReportMoveLines} from "../AccountReportMoveLines/accountReportMoveLines.esm";
import {Component} from "@odoo/owl";
import {Dropdown} from "@web/core/dropdown/dropdown";
import {formatMonetary} from "@web/views/fields/formatters";
import {useService} from "@web/core/utils/hooks";

export class AccountReportLines extends Component {
    static template = "account_financial_report.AccountReportLines";
    static components = {
        Dropdown,
        AccountReportMoveLines,
    };
    static props = {
        row: Object,
        columns: Object,
    };

    setup() {
        super.setup();
        this.action = useService("action");
    }

    get columns() {
        return this.props.columns;
    }
    get row() {
        return this.props.row;
    }

    currentRow(column) {
        return this.row.values.find((val) => val.key === column.key);
    }

    formatValue(value, type, currencyId) {
        switch (type) {
            case "monetary":
                return formatMonetary(value, {currencyId: currencyId});
            default:
                return value;
        }
    }
}
