# © 2018 Forest and Biomass Romania SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.tools import SQL


class AccountGroup(models.Model):
    _inherit = "account.group"

    group_child_ids = fields.One2many(
        comodel_name="account.group", inverse_name="parent_id", string="Child Groups"
    )
    level = fields.Integer(compute="_compute_level", recursive=True)
    account_ids = fields.One2many(
        comodel_name="account.account",
        compute="_compute_account_ids",
        string="Accounts",
        store=False,
    )
    compute_account_ids = fields.Many2many(
        "account.account",
        recursive=True,
        compute="_compute_group_accounts",
        string="Compute accounts",
        store=False,
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

    @api.depends("code_prefix_start", "code_prefix_end")
    def _compute_account_ids(self):
        """Retrieves every account from `self`.
        In Odoo 18 the group_id on account is not stored so it raises
        an error the one2many account_ids with inverse name group_id."""
        self.account_ids = self.env["account.account"]
        if not self.ids:
            return
        root_company_id = self.env.company.root_id.id
        results = self.env.execute_query(
            SQL(
                """
                    SELECT
                        account_groups.group_id,
                        ARRAY_AGG(account_groups.account_id)
                    FROM (
                        SELECT DISTINCT ON (a.id)
                            a.id AS account_id,
                            g.id AS group_id
                        FROM account_account a
                        JOIN account_group g ON
                            g.code_prefix_start <=
                            LEFT(a.code_store->>%(root_company_id)s,
                            char_length(g.code_prefix_start))
                            AND g.code_prefix_end >=
                            LEFT(a.code_store->>%(root_company_id)s,
                            char_length(g.code_prefix_end))
                            AND g.company_id = %(root_company_id_int)s
                        ORDER BY a.id, char_length(g.code_prefix_start) DESC
                    ) account_groups
                    WHERE account_groups.group_id IN %(group_ids)s
                    GROUP BY account_groups.group_id
                """,
                root_company_id=str(root_company_id),
                root_company_id_int=root_company_id,
                group_ids=tuple(self.ids),
            )
        )
        group_by_code = dict(results)
        if not group_by_code:
            return
        for record in self:
            record.account_ids = group_by_code.get(record.id, [])

    @api.depends("code_prefix_start", "parent_id.complete_code")
    def _compute_complete_code(self):
        """Forms complete code of location from parent location to child location."""
        for group in self:
            if group.parent_id.complete_code:
                group.complete_code = (
                    f"{group.parent_id.complete_code}/{group.code_prefix_start}"
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
        "group_child_ids.compute_account_ids",
    )
    def _compute_group_accounts(self):
        for one in self:
            one.compute_account_ids = (
                one.account_ids | one.group_child_ids.compute_account_ids
            )
