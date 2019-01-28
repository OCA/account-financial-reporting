odoo.define('account_financial_report.account_financial_report_backend', function (require) {
    'use strict';

    var core = require('web.core');
    var Widget = require('web.Widget');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var ReportWidget = require(
        'account_financial_report.account_financial_report_widget'
        );


    var report_backend = Widget.extend(ControlPanelMixin, {
        // Stores all the parameters of the action.
        events: {
            'click .o_account_financial_reports_print': 'print',
            'click .o_account_financial_reports_export': 'export',
        },
        init: function (parent, action) {
            this.actionManager = parent;
            this.given_context = {};
            this.odoo_context = action.context;
            this.controller_url = action.context.url;
            if (action.context.context) {
                this.given_context = action.context.context;
            }
            this.given_context.active_id = action.context.active_id || 
                action.params.active_id;
            this.given_context.model = action.context.active_model || false;
            this.given_context.ttype = action.context.ttype || false;
            return this._super.apply (this, arguments);
        },
        willStart: function () {
            return $.when(this.get_html());
        },
        set_html: function () {
            var self = this;
            var def = $.when();
            if (!this.report_widget) {
                this.report_widget = new ReportWidget(this, this.given_context);
                def = this.report_widget.appendTo(this.$el);
            }
            def.then(function () {
                self.report_widget.$el.html(self.html);
            });
        },
        start: function() {
            this.set_html();
            return this._super();
        },
        // Fetches the html and is previous report.context if any, else create it
        get_html: function() {
            var self = this;
            var defs = [];
            return this._rpc({
                model: this.given_context.model,
                method: 'get_html',
                args: [self.given_context],
                context: self.odoo_context,
            })
            .then(function (result) {
                self.html = result.html;
                defs.push(self.update_cp());
                return $.when.apply($, defs);
            });
        },
        // Updates the control panel and render the elements that have yet 
        // to be rendered
        update_cp: function () {
            if (this.$buttons) {
                var status = {
                    breadcrumbs: this.actionManager.get_breadcrumbs(),
                    cp_content: {$buttons: this.$buttons},
                };
                return this.update_control_panel(status);
            }
        },
        do_show: function () {
            this._super();
            this.update_cp();
        },
        print: function () {
            var self = this;
            this._rpc({
                model: this.given_context.model,
                method: 'print_report',
                args: [this.given_context.active_id, 'qweb-pdf'],
                context: self.odoo_context,
            }).then(function(result){
                self.do_action(result);
            });
        },
        export: function () {
            var self = this;
            this._rpc({
                model: this.given_context.model,
                method: 'print_report',
                args: [this.given_context.active_id, 'xlsx'],
                context: self.odoo_context,
            })
            .then(function(result){
                self.do_action(result);
            });
        },
    });

    core.action_registry.add(
        "account_financial_report_backend",
        report_backend
        );
    return report_backend;
});
