# © 2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class WizardOpenTaxBalances(models.TransientModel):
    _name = 'wizard.open.tax.balances'
    _description = 'Wizard Open Tax Balances'

    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda self: self.env.user.company_id)
    from_date = fields.Date('From date', required=True)
    to_date = fields.Date('To date', required=True)
    date_range_id = fields.Many2one('date.range', 'Date range')
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries'),
    ], 'Target Moves', required=True, default='posted')

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        if self.date_range_id:
            self.from_date = self.date_range_id.date_start
            self.to_date = self.date_range_id.date_end
        else:
            self.from_date = self.to_date = None

    @api.multi
    def open_taxes(self):
        self.ensure_one()
        action = self.env.ref('account_tax_balance.action_tax_balances_tree')
        act_vals = action.read()[0]
        # override action name doesn't work in v12 or v10
        # we need to build a dynamic action on main keys
        vals = {x: act_vals[x] for x in act_vals
                if x in ('res_model', 'view_mode', 'domain',
                         'view_id', 'search_view_id', 'name', 'type')}
        lang = self.env['res.lang'].search(
            [('code', '=', self.env.user.lang or 'en_US')])
        date_format = lang and lang.date_format or "%m/%d/%Y"
        infos = {'name': vals['name'], 'target': _(self.target_move),
                 'from': self.from_date.strftime(date_format),
                 'to': self.to_date.strftime(date_format),
                 'company': self.company_id.name}
        # name of action which is displayed in breacrumb
        vals["name"] = _(
            "%(name)s: %(target)s from %(from)s to %(to)s") % infos
        multi_cpny_grp = self.env.ref('base.group_multi_company')
        if multi_cpny_grp in self.env.user.groups_id:
            vals['name'] = '%s (%s)' % (vals['name'], self.company_id.name)
        vals['context'] = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'target_move': self.target_move,
            'company_id': self.company_id.id,
        }
        return vals
