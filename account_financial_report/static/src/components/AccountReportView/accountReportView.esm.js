// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {Component, onWillStart, useState} from "@odoo/owl";
import {AccountReportContent} from "./AccountReportContent/accountReportContent.esm";
import {AccountReportHeader} from "./AccountReportHeader/accountReportHeader.esm";
import {Layout} from "@web/search/layout";
import {getReportController} from "./AccountReportController/reportControllerLoader.esm";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class AccountReportView extends Component {
    static template = "account_financial_report.AccountReportView";

    static components = {
        AccountReportHeader,
        AccountReportContent,
        Layout,
    };

    setup() {
        this.orm = useService("orm");
        this.ui = useService("ui");
        this.action = useService("action");
        this.env = useState({
            exportReport: this.exportReport.bind(this),
            exporting: false,
            pagination: {
                offset: 0,
                limit: 10,
            },
        });
        this.params = this.props.action.params;
        onWillStart(async () => await this.loadReport());
    }

    async exportReport(format) {
        const methods = {
            pdf: "button_export_pdf",
            xlsx: "button_export_xlsx",
        };
        if (!methods[format] || this.env.exporting) {
            return;
        }
        this.env.exporting = true;
        try {
            const action = await this.orm.call(
                this.params.model,
                methods[format],
                [[this.params.active_id]],
                {context: this.props.action.context || {}}
            );
            await this.action.doAction(action);
        } finally {
            this.env.exporting = false;
        }
    }

    async loadReport() {
        this.ui.block();
        try {
            const datas = await this.orm.call(
                this.params.report_model,
                "get_report_values",
                [[this.params.active_id], this.params.data]
            );
            console.log(datas);
            const [vals] = await Promise.all([this._prepareVals(datas)]);
            Object.assign(this.env, vals);
        } finally {
            this.ui.unblock();
        }
    }

    async _prepareVals(datas) {
        const Controller = getReportController(
            this.params.report_type,
            datas,
            this.params
        );
        return await Controller.adapt();
    }
}

registry.category("actions").add("account_report_view", AccountReportView);
