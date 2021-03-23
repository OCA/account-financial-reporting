odoo.define("account_financial_report.ReportActionManager", function(require) {
    "use strict";

    const ActionManager = require("web.ActionManager");
    require("web.ReportActionManager");

    ActionManager.include({
        /**
         * @override
         */
        _executeReportClientAction: function(action, options) {
            const MODULE_NAME = "account_financial_report";

            // When 'report_action' is called from the backend, Odoo hardcodes the action tag.
            // We have to make a hack to use our own report controller.
            if (action.report_file.startsWith(`${MODULE_NAME}.`)) {
                const urls = this._makeReportUrls(action);
                const clientActionOptions = _.extend({}, options, {
                    context: action.context,
                    data: action.data,
                    display_name: action.display_name,
                    name: action.name,
                    report_file: action.report_file,
                    report_name: action.report_name,
                    report_url: urls.html,
                });
                return this.doAction(
                    "account_financial_report.client_action",
                    clientActionOptions
                );
            }
            return this._super.apply(this, arguments);
        },
    });
});
