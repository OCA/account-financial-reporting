# -*- coding: utf-8 -*-
# © 2015 Yannick Vaucher (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).-
from openerp import models, fields, api, _, exceptions


class AccountFiscalyear(models.Model):
    _name = 'account.fiscalyear'

    _order = 'start_date DESC'

    name = fields.Char(required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda rec: rec.env.user.company_id,
    )
    state = fields.Selection(
        [('draft', 'Open'),
         ('done', 'Closed')],
        required=True,
        readonly=True,
        copy=False,
        default='draft',
    )

    @api.one
    @api.constrains('start_date', 'end_date')
    def _check_estimated_times(self):
        if (self.start_date and self.end_date and
                self.start_date > self.end_date):
            raise exceptions.ValidationError(
                _('End date cannot be set before Start date.'))
