# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MisBudget(models.Model):

    _name = 'mis.budget'
    _description = 'MIS Budget'

    # TODO chatter, track state, name, description

    name = fields.Char(
        required=True,
    )
    description = fields.Char(
    )
    report_id = fields.Many2one(
        comodel_name='mis.report',
        string='MIS Report Template',
        required=True,
    )
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date range',
    )
    date_from = fields.Date(
        required=True,
        string='From',
    )
    date_to = fields.Date(
        required=True,
        string='To',
    )
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirmed', 'Confirmed'),
         ('validated', 'Validated')],
        required=True,
        default='draft'
    )
    item_ids = fields.One2many(
        comodel_name='mis.budget.item',
        inverse_name='budget_id',
        copy=True
    )

    @api.onchange('date_range_id')
    def _onchange_date_range(self):
        for rec in self:
            if rec.date_range_id:
                rec.date_from = rec.date_range_id.date_start
                rec.date_to = rec.date_range_id.date_end

    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        for rec in self:
            if rec.date_range_id:
                if rec.date_from != rec.date_range_id.date_start or \
                        rec.date_to != rec.date_range_id.date_end:
                    rec.date_range_id = False
