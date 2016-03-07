openerp.mis_builder_analytic_filter = function(instance) {
    var _t = instance.web._t;

    instance.mis_builder.MisReport.include({

        init: function() {
            this._super.apply(this, arguments);
            this.account_analytic_id = false;
            this.initialized = false;
            this.mis_report_instance_id = false;
        },
        initialize_field: function() {
            var self = this;
            self.destroy_content();
            self.init_fields();
        },
        destroy_content: function() {
            if (this.dfm) {
                this.dfm.destroy();
                this.dfm = undefined;
            }
        },
        get_context: function() {
            var self = this;
            context = this._super.apply(this, arguments);
            context['account_analytic_id'] = this.account_analytic_id;
            return context
        },
        init_fields: function() {
            var self = this;
            if (self.dfm)
                return;
            self.$(".oe_mis_builder_analytic_axis").show();
            self.dfm = new instance.web.form.DefaultFieldManager(self);
            self.dfm.extend_field_desc({
                account: {
                    relation: "account.analytic.account",
                },
            });
            self.account_m2o = new instance.web.form.FieldMany2One(self.dfm, {
                attrs: {
                    placeholder: _t("Analytic Account"),
                    name: "account",
                    type: "many2one",
                    domain: [],
                    context: {},
                    modifiers: '{}',
                },
            });
            if (this.initialized) {
                self.account_m2o.set('value', this.account_analytic_id);
            } else {
                val = self.getParent().dataset.context.account_analytic_id
                if (val) {
                    self.account_m2o.set('value', val);
                    this.account_analytic_id = val
                }
                this.initialized = true;
            }
            self.account_m2o.prependTo(self.$(".oe_mis_builder_analytic_axis"));
            self.account_m2o.$input.focusout(function(){
                self.account_analytic_id = self.account_m2o.get_value();
            });
            self.$(".oe_mis_builder_generate_content").click(_.bind(this.generate_content, this));
        },
        renderElement: function() {
            this._super();
            var self = this;
            self.initialize_field();
        },

});
}
