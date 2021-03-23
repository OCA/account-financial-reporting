odoo.define("account_financial_report.client_action", function (require) {
    "use strict";

    var ReportAction = require("report.client_action");
    var core = require("web.core");

    var QWeb = core.qweb;

    const AFRReportAction = ReportAction.extend({
        start: function () {
            return this._super.apply(this, arguments).then(() => {
                this.$buttons = $(
                    QWeb.render(
                        "account_financial_report.client_action.ControlButtons",
                        {}
                    )
                );
                this.$buttons.on("click", ".o_report_print", this.on_click_print);
                this.$buttons.on("click", ".o_report_export", this.on_click_export);

                this.controlPanelProps.cp_content = {
                    $buttons: this.$buttons,
                };

                this._controlPanelWrapper.update(this.controlPanelProps);
            });
        },

        on_click_export: function () {
            const action = {
                type: "ir.actions.report",
                report_type: "xlsx",
                report_name: this._get_xlsx_name(this.report_name),
                report_file: this._get_xlsx_name(this.report_file),
                data: this.data,
                context: this.context,
                display_name: this.title,
            };
            return this.do_action(action);
        },

        /**
         * @param {String} str
         * @returns {String}
         */
        _get_xlsx_name: function (str) {
            if (!_.isString(str)) {
                return str;
            }
            const parts = str.split(".");
            return `a_f_r.report_${parts[parts.length - 1]}_xlsx`;
        },
    });

    core.action_registry.add("account_financial_report.client_action", AFRReportAction);

    return AFRReportAction;
});
