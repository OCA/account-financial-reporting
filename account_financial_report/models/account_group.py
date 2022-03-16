# © 2018 Forest and Biomass Romania SA
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
        if self.parent_id.complete_name:
            self.complete_name = "{}/{}".format(self.parent_id.complete_name, self.name)
        else:
            self.complete_name = self.name

    @api.depends("code_prefix_start", "parent_id.complete_code")
    def _compute_complete_code(self):
        """Forms complete code of location from parent location to child location."""
        if self.parent_id.complete_code:
            self.complete_code = "{}/{}".format(
                self.parent_id.complete_code, self.code_prefix_start
            )
        else:
            self.complete_code = self.code_prefix_start

    @api.depends("parent_id", "parent_id.level")
    def _compute_level(self):
        for group in self:
            if not group.parent_id:
                group.level = 0
            else:
                group.level = group.parent_id.level + 1

    @api.depends(
        "code_prefix_start",
        "account_ids",
        "account_ids.code",
        "group_child_ids",
        "group_child_ids.account_ids.code",
    )
    def _compute_group_accounts(self):
        account_obj = self.env["account.account"]
        accounts = account_obj.search([])
        for group in self:
            prefix = group.code_prefix_start if group.code_prefix_start else group.name
            gr_acc = accounts.filtered(lambda a: a.code.startswith(prefix)).ids
            group.compute_account_ids = [(6, 0, gr_acc)]
