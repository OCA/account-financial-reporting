odoo.define('mis.builder', function (require) {
"use strict";

var core = require('web.core');
var form_common = require('web.form_common');
var Model = require('web.DataModel');
var data = require('web.data');
var ActionManager = require('web.ActionManager');

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
        this.mis_report_instance_id = false;
        this.field_manager.on("view_content_has_changed", this, this.reload_widget);
    },

    initialize_field: function() {
        var self = this;
        self.destroy_content();
        self.init_fields();
    },

    init_fields: function() {
        var self = this;
        if (self.dfm)
            return;
        self.dfm = new form_common.DefaultFieldManager(self);
        self.$(".oe_mis_builder_generate_content").click(_.bind(this.generate_content, this));
    },

    destroy_content: function() {
        if (this.dfm) {
            this.dfm.destroy();
            this.dfm = undefined;
        }
    },

    reload_widget: function() {

    },

    start: function() {
        this._super.apply(this, arguments);
        var self = this;
        self.mis_report_instance_id = self.getParent().datarecord.id;
        if (self.mis_report_instance_id) {
            self.getParent().dataset.context.no_destroy = true;
            self.generate_content();
        }
    },

    get_context: function() {
        var self = this;
        var context = {};
        if (this.mis_report_instance_id){
            context.active_ids = [this.mis_report_instance_id];
        }
        return context;
    },

    print: function() {
        var self = this;
        var context = new data.CompoundContext(self.build_context(), self.get_context()|| {});
        new Model("mis.report.instance").call(
            "print_pdf",
            [self.mis_report_instance_id],
            {'context': context}
        ).then(function(result){
            self.do_action(result);
        });
    },
    export_pdf: function() {
        var self = this;
        var context = new data.CompoundContext(self.build_context(), self.get_context()|| {});
        new Model("mis.report.instance").call(
            "export_xls",
            [self.mis_report_instance_id],
            {'context': context}
        ).then(function(result){
            self.do_action(result);
        });
    },
    display_settings: function() {
        var self = this;
        var context = new data.CompoundContext(self.build_context(), self.get_context()|| {});
        new Model("mis.report.instance").call(
            "display_settings",
            [self.mis_report_instance_id],
            {'context': context}
        ).then(function(result){
            self.do_action(result);
        });
    },
    generate_content: function() {
        var self = this;
        var context = new data.CompoundContext(self.build_context(), self.get_context()|| {});
        new Model("mis.report.instance").call(
            "compute",
            [self.mis_report_instance_id],
            {'context': context}
        ).then(function(result){
            self.mis_report_data = result;
            self.renderElement();
        });
    },
    renderElement: function() {
        this._super();
        var self = this;
        self.$(".oe_mis_builder_print").click(_.bind(this.print, this));
        self.$(".oe_mis_builder_export").click(_.bind(this.export_pdf, this));
        self.$(".oe_mis_builder_settings").click(_.bind(this.display_settings, this));
        var Users = new Model('res.users');
        Users.call('has_group', ['account.group_account_user']).done(function (res) {
            if (res) {
                self.$(".oe_mis_builder_settings").show();
            }
        });
        self.initialize_field();
    },
    events: {
        "click a.mis_builder_drilldown": "drilldown",
    },

    drilldown: function(event) {
        var self = this;
        var context = new data.CompoundContext(self.build_context(), self.get_context()|| {});
        var drilldown = $(event.target).data("drilldown");
        if (drilldown) {
            new Model("mis.report.instance").call(
                "drilldown",
                [self.mis_report_instance_id, drilldown],
                {'context': context}
            ).then(function(result) {
                if (result) {
                    self.do_action(result);
                }
            });
        }
    },
});

ActionManager.include({
    /*
     * In the case where we would be open in modal view, this is
     * necessary to avoid to close the popup on click on button like print,
     * export, ...
     */
    dialog_stop: function (reason) {
        var self = this;
        if (self.dialog_widget && self.dialog_widget.dataset && self.dialog_widget.dataset.context) {
            var context = self.dialog_widget.dataset.context;
            if (!context.no_destroy) {
                this._super.apply(this, arguments);
            }
        } else {
            this._super.apply(this, arguments);
        }
    }
});
core.form_custom_registry.add('mis_report', MisReport);

return {
    MisReport: MisReport,
};

});
