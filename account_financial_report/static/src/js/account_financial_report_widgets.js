odoo.define('account_financial_report.account_financial_report_widget', function
(require) {
    'use strict';

    var Widget = require('web.Widget');


    var accountFinancialReportWidget = Widget.extend({
        events: {
            'click .o_account_financial_reports_web_action':
                'boundLink',
            'click .o_account_financial_reports_web_action_multi':
                'boundLinkmulti',
            'click .o_account_financial_reports_web_action_monetary':
                'boundLinkMonetary',
            'click .o_account_financial_reports_web_action_monetary_multi':
                'boundLinkMonetarymulti',
        },
        init: function () {
            this._super.apply(this, arguments);
        },
        start: function () {
            return this._super.apply(this, arguments);
        },
        boundLink: function (e) {
            var res_model = $(e.target).data('res-model');
            var res_id = $(e.target).data('active-id');
            return this.do_action({
                type: 'ir.actions.act_window',
                res_model: res_model,
                res_id: res_id,
                views: [[false, 'form']],
                target: 'current',
            });
        },
        boundLinkmulti: function (e) {
            var res_model = $(e.target).data('res-model');
            var domain = $(e.target).data('domain');
            if (!res_model) {
                res_model = $(e.target.parentElement).data('res-model');
            }
            if (!domain) {
                domain = $(e.target.parentElement).data('domain');
            }
            return this.do_action({
                type: 'ir.actions.act_window',
                name: this._toTitleCase(res_model.split('.').join(' ')),
                res_model: res_model,
                domain: domain,
                views: [[false, "list"], [false, "form"]],
                target: 'current',
            });
        },
        boundLinkMonetary: function (e) {
            var res_model = $(e.target.parentElement).data('res-model');
            var res_id = $(e.target.parentElement).data('active-id');
            return this.do_action({
                type: 'ir.actions.act_window',
                res_model: res_model,
                res_id: res_id,
                views: [[false, 'form']],
                target: 'current',
            });
        },
        boundLinkMonetarymulti: function (e) {
            var res_model = $(e.target.parentElement).data('res-model');
            var domain = $(e.target.parentElement).data('domain');
            return this.do_action({
                type: 'ir.actions.act_window',
                res_model: res_model,
                domain: domain,
                views: [[false, "list"], [false, "form"]],
                target: 'current',
            });
        },
        _toTitleCase: function(str) {
            return str.replace(/\w\S*/g, function(txt){
                return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
            });
        },
    });

    return accountFinancialReportWidget;

});
