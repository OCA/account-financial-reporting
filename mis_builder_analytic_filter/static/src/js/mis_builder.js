/* © 2016 ACSONE SA/NV
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
 */

odoo.define('mis.builder.analytic.filter', function (require) {
"use strict";

var Model = require('web.DataModel');
var core = require('web.core');
var _t = core._t;
var form_common = require('web.form_common');
var MisBuilderWidget = require('mis.builder');
var MisReport = MisBuilderWidget.MisReport;
var FieldMany2One = core.form_widget_registry.get('many2one');

MisReport.include({
    init: function() {
        this._super.apply(this, arguments);
        this.account_analytic_id = false;
        this.analytic_account_initialized = false;
    },

    get_context: function() {
        var self = this;
        var context = this._super.apply(this, arguments);
        context['account_analytic_id'] = this.account_analytic_id;
        return context
    },

    init_fields: function() {
        this._super.apply(this, arguments);
        var self = this;
        var Users = new Model('res.users');
        Users.call('has_group', ['analytic.group_analytic_accounting']).done(function (res) {
            if (res) {
                self.$(".oe_mis_builder_analytic_account").css('visibility', 'visible');
            }
        });
        self.dfm.extend_field_desc({
            account: {
                relation: "account.analytic.account",
            },
        });
        self.account_m2o = new FieldMany2One(self.dfm, {
            attrs: {
                placeholder: _t("Analytic Account"),
                name: "account",
                type: "many2one",
                domain: [],
                context: {},
                modifiers: '{}',
            },
        });
        if (this.analytic_account_initialized) {
            self.account_m2o.set('value', this.account_analytic_id);
        } else {
            var val = self.getParent().dataset.context.account_analytic_id;
            if (val) {
                self.account_m2o.set('value', val);
                this.account_analytic_id = val
            }
            this.analytic_account_initialized = true;
        }
        self.account_m2o.prependTo(self.$(".oe_mis_builder_analytic_account"));
        self.account_m2o.$input.focusout(function(){
            self.account_analytic_id = self.account_m2o.get_value();
        });
    }
});

});
