# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class MisBudget(models.Model):

    _name = 'mis.budget'
    _description = 'MIS Budget'
    _inherit = ['mail.thread']

    name = fields.Char(
        required=True,
        track_visibility='onchange',
    )
    description = fields.Char(
        track_visibility='onchange',
    )
    report_id = fields.Many2one(
        comodel_name='mis.report',
        string='MIS Report Template',
        required=True,
    )
    fiscalyear_id = fields.Many2one(
        comodel_name='account.fiscalyear',
        string='Fiscal Year',
    )
    date_from = fields.Date(
        required=True,
        string='From',
        track_visibility='onchange',
    )
    date_to = fields.Date(
        required=True,
        string='To',
        track_visibility='onchange',
    )
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirmed', 'Confirmed'),
         ('cancelled', 'Cancelled')],
        required=True,
        default='draft',
        track_visibility='onchange',
    )
    item_ids = fields.One2many(
        comodel_name='mis.budget.item',
        inverse_name='budget_id',
        copy=True,
    )

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if 'name' not in default:
            default['name'] = _("%s (copy)") % self.name
        return super(MisBudget, self).copy(default=default)

    @api.onchange('fiscalyear_id')
    def _onchange_fiscalyear_id(self):
        for rec in self:
            if rec.fiscalyear_id:
                rec.date_from = rec.fiscalyear_id.date_start
                rec.date_to = rec.fiscalyear_id.date_stop

    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        for rec in self:
            if rec.fiscalyear_id:
                if rec.date_from != rec.fiscalyear_id.date_start or \
                        rec.date_to != rec.fiscalyear_id.date_stop:
                    rec.fiscalyear_id = False

    @api.multi
    def action_draft(self):
        for rec in self:
            self.state = 'draft'

    @api.multi
    def action_cancel(self):
        for rec in self:
            self.state = 'cancelled'

    @api.multi
    def action_confirm(self):
        for rec in self:
            self.state = 'confirmed'
