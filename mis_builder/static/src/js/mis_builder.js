odoo.define('mis.builder', function (require) {
"use strict";

var core = require('web.core');
var form_common = require('web.form_common');
var Model = require('web.DataModel');
var data = require('web.data');

var MisReport = form_common.FormWidget.extend({
    /**
     * @constructs instance.mis_builder.MisReport
     * @extends instance.web.form.FormWidget
     * 
     */
    template: "mis_builder.MisReport",
    init: function() {
        this._super.apply(this, arguments);
        this.mis_report_data = null;
    },

    start: function() {
        this._super.apply(this, arguments);
        var self = this;
        new Model("mis.report.instance").call(
            "compute", 
            [self.getParent().dataset.context.active_id], 
            {'context': new data.CompoundContext()}
        ).then(function(result){
            self.mis_report_data = result;
            self.renderElement();
        });
    },

    events: {
        "click a.mis_builder_drilldown": "drilldown",
    },

    drilldown: function(event) {
        var self = this;
        var drilldown = JSON.parse($(event.target).data("drilldown"));
        if (drilldown) {
            var period_id = JSON.parse($(event.target).data("period-id"));
            var val_c = JSON.parse($(event.target).data("expr"));
            new Model("mis.report.instance.period").call(
                "drilldown",
                [period_id, val_c],
                {'context': new data.CompoundContext()}
            ).then(function(result) {
                if (result) {
                    self.do_action(result);
                }
            });
        }
    },
});

core.form_custom_registry.add('mis_report', MisReport);

});
