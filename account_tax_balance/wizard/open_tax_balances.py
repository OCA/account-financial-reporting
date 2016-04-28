# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class OpenTaxBalances(models.TransientModel):
    _name = 'wizard.open.tax.balances'
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
        vals = action.read()[0]
        vals['context'] = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'target_move': self.target_move,
            'company_id': self.company_id.id,
        }
        return vals
