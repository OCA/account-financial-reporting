openerp.mis_builder = function(instance) {

    instance.mis_builder.MisReport = instance.web.form.FormWidget.extend({
        template: "mis_builder.MisReport",

        init: function() {
            this._super.apply(this, arguments);
            this.mis_report_data = null;
        },

        start: function() {
            this._super.apply(this, arguments);
            var self = this;
            new instance.web.Model("mis.report.instance").call(
                "compute", 
                [self.getParent().dataset.context.active_id], 
                {'context': new instance.web.CompoundContext()}
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
                new instance.web.Model("mis.report.instance.period").call(
                    "drilldown",
                    [period_id, val_c],
                    {'context': new instance.web.CompoundContext()}
                ).then(function(result) {
                    if (result) {
                        self.do_action(result);
                    }
                });
            }
        },
    });

    instance.web.form.custom_widgets.add('mis_report', 'instance.mis_builder.MisReport');
}
