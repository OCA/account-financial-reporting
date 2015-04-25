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
            var val_c = JSON.parse($(event.target).data("val-c"));
            var val =  JSON.parse($(event.target).data("val"));
            var period_id = JSON.parse($(event.target).data("period-id"));
            var period_name = JSON.parse($(event.target).data("period-name"));
            var self = this;
            if (!(val === null) && (val_c.indexOf('bal') >=0)){
                new instance.web.Model("mis.report.instance.period").call(
                    "compute_domain", 
                    [period_id, val_c],
                    {'context': new instance.web.CompoundContext()}
                ).then(function(result){
                    if (result != false){
                        self.do_action({
                            name: val_c + ' - ' + period_name,
                            domain: JSON.stringify(result),
                            type: 'ir.actions.act_window',
                            res_model: "account.move.line",
                            views: [[false, 'list'], [false, 'form']],
                            view_type : "list",
                            view_mode : "list",
                            target: 'current',
                        });
                    }
                });
            }
        },
    });

    instance.web.form.custom_widgets.add('mis_report', 'instance.mis_builder.MisReport');
}