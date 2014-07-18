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
	});
	
	instance.web.form.custom_widgets.add('mis_report', 'instance.mis_builder.MisReport');
}