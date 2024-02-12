# Copyright 2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class WizardOpenTaxBalances(models.TransientModel):
    _name = "wizard.open.tax.balances"
    _description = "Wizard Open Tax Balances"

    company_ids = fields.Many2many(
        comodel_name="res.company",
        string="Companies",
        required=True,
        domain=lambda self: [("id", "in", self.env.companies.ids)],
        default=lambda self: self.env.companies.ids,
    )
    from_date = fields.Date(
        required=True, store=True, readonly=False, compute="_compute_date_range"
    )
    to_date = fields.Date(
        required=True, store=True, readonly=False, compute="_compute_date_range"
    )
    date_range_id = fields.Many2one("date.range")
    target_move = fields.Selection(
        [("posted", "All Posted Entries"), ("all", "All Entries")],
        "Target Moves",
        required=True,
        default="posted",
    )

    @api.depends("date_range_id")
    def _compute_date_range(self):
        for wizard in self:
            if wizard.date_range_id:
                wizard.from_date = wizard.date_range_id.date_start
                wizard.to_date = wizard.date_range_id.date_end
            else:
                wizard.from_date = wizard.to_date = None

    def open_taxes(self):
        self.ensure_one()
        action = self.env.ref("account_tax_balance.action_tax_balances_tree")
        act_vals = action.sudo().read()[0]
        # override action name doesn't work in v12 or v10
        # we need to build a dynamic action on main keys
        vals = {
            x: act_vals[x]
            for x in act_vals
            if x
            in (
                "res_model",
                "view_mode",
                "domain",
                "view_id",
                "search_view_id",
                "name",
                "type",
            )
        }
        lang = self.env["res.lang"].search(
            [("code", "=", self.env.user.lang or "en_US")]
        )
        date_format = lang and lang.date_format or "%m/%d/%Y"
        infos = {
            "name": vals["name"],
            "target": _(self.target_move),
            "from": self.from_date.strftime(date_format),
            "to": self.to_date.strftime(date_format),
        }
        # name of action which is displayed in breacrumb
        vals["name"] = _("%(name)s: %(target)s from %(from)s to %(to)s") % infos
        multi_cpny_grp = self.env.ref("base.group_multi_company")
        if multi_cpny_grp in self.env.user.groups_id:
            company_names = self.company_ids.mapped("name")
            vals["name"] = "{} ({})".format(vals["name"], ", ".join(company_names))
        vals["context"] = {
            "from_date": self.from_date,
            "to_date": self.to_date,
            "target_move": self.target_move,
            "company_ids": self.company_ids.ids,
        }
        return vals
