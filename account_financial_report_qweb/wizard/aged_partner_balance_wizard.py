# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class AccountAgedTrialBalance(models.TransientModel):

    _name = 'account.aged.trial.balance.wizard'
    _description = 'Aged partner balanced'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company')
    date_from = fields.Date('Date from')
    date_to = fields.Date('Date to')

    partner_ids = fields.Many2many(
        'res.partner',
        string='Filter on partner',
        help='Only selected partners will be printed. '
        'Leave empty to print all partners.')
