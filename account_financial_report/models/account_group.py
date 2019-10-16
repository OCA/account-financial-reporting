# © 2018 Forest and Biomass Romania SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountGroup(models.Model):
    _inherit = 'account.group'

    group_child_ids = fields.One2many(
        comodel_name='account.group',
        inverse_name='parent_id',
        string='Child Groups')
    level = fields.Integer(
        string='Level',
        compute='_compute_level',
        store=True)
    account_ids = fields.One2many(
        comodel_name='account.account',
        inverse_name='group_id',
        string="Accounts")
    compute_account_ids = fields.Many2many(
        'account.account',
        compute='_compute_group_accounts',
        string="Compute accounts", store=True)

    @api.multi
    @api.depends('parent_id', 'parent_id.level')
    def _compute_level(self):
        for group in self:
            if not group.parent_id:
                group.level = 0
            else:
                group.level = group.parent_id.level + 1

    @api.multi
    @api.depends('code_prefix', 'account_ids', 'account_ids.code',
                 'group_child_ids', 'group_child_ids.account_ids.code')
    def _compute_group_accounts(self):
        account_obj = self.env['account.account']
        accounts = account_obj.search([])
        for group in self:
            prefix = group.code_prefix if group.code_prefix else group.name
            gr_acc = accounts.filtered(
                lambda a: a.code.startswith(prefix)).ids
            group.compute_account_ids = [(6, 0, gr_acc)]
