# ?? 2018 Forest and Biomass Romania SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountGroup(models.Model):
    _inherit = "account.group"

    group_child_ids = fields.One2many(
        comodel_name="account.group", inverse_name="parent_id", string="Child Groups"
    )
    level = fields.Integer(compute="_compute_level", recursive=True)
    account_ids = fields.One2many(
        comodel_name="account.account", inverse_name="group_id", string="Accounts"
    )
    compute_account_ids = fields.Many2many(
        "account.account",
        recursive=True,
        compute="_compute_group_accounts",
        string="Compute accounts",
        store=True,
    )
    complete_name = fields.Char(
        "Full Name", compute="_compute_complete_name", recursive=True
    )
    complete_code = fields.Char(
        "Full Code", compute="_compute_complete_code", recursive=True
    )

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        """Forms complete name of location from parent location to child location."""
        for group in self:
            if group.parent_id.complete_name:
                group.complete_name = f"{group.parent_id.complete_name}/{group.name}"
            else:
                group.complete_name = group.name

    @api.depends("code_prefix_start", "parent_id.complete_code")
    def _compute_complete_code(self):
        """Forms complete code of location from parent location to child location."""
        for group in self:
            if group.parent_id.complete_code:
                group.complete_code = "{}/{}".format(
                    group.parent_id.complete_code, group.code_prefix_start
                )
            else:
                group.complete_code = group.code_prefix_start

    @api.depends("parent_id", "parent_id.level")
    def _compute_level(self):
        for group in self:
            if not group.parent_id:
                group.level = 0
            else:
                group.level = group.parent_id.level + 1

    @api.depends(
        "account_ids",
        "group_child_ids.compute_account_ids",
    )
    def _compute_group_accounts(self):
        for one in self:
            one.compute_account_ids = (
                one.account_ids | one.group_child_ids.compute_account_ids
            )
