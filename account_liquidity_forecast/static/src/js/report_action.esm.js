/** @odoo-module **/

import {ReportAction} from "@web/webclient/actions/reports/report_action";
import {useEnrichWithActionLinks} from "./report.esm";
import {patch} from "@web/core/utils/patch";

// Define the module name
const MODULE_NAME = "account_liquidity_forecast";

// Extend ReportAction class
patch(ReportAction.prototype, {
    setup() {
        super.setup(...arguments);
        this.isAccountLiquidityFinancialReport = this.props.report_name.startsWith(
            `${MODULE_NAME}.`
        );
        useEnrichWithActionLinks(this.iframe);
    },

    export_liquidity_forecast_report() {
        this.env.services.action.doAction({
            type: "ir.actions.report",
            report_type: "xlsx",
            report_name: this._get_liquidity_forecast_xlsx_name(this.props.report_name),
            report_file: this._get_liquidity_forecast_xlsx_name(this.props.report_file),
            data: this.props.data || {},
            context: this.props.context || {},
            display_name: this.title,
        });
    },

    /**
     * @param {String} str
     * @returns {String}
     */
    _get_liquidity_forecast_xlsx_name(str) {
        if (typeof str !== "string") {
            return str;
        }
        return `report_liquidity_forecast_xlsx`;
    },
});
