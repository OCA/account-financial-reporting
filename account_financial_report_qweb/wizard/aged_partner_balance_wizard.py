# -*- coding: utf-8 -*-
# Author: Damien Crier, Andrea Stirpe, Kevin Graveman, Dennis Sluijk
# Copyright 2016 Camptocamp SA, Onestein B.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from openerp.exceptions import Warning as UserError
from openerp import api, fields, models


class AccountAgedTrialBalance(models.TransientModel):

    _name = 'account.aged.trial.balance.wizard'
    _description = 'Aged partner balanced'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda s: s.env.user.company_id
    )
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')],
                                   string='Target Moves',
                                   required=True,
                                   default='posted')
    result_selection = fields.Selection(
        [('customer', 'Receivable Accounts'),
         ('supplier', 'Payable Accounts'),
         ('customer_supplier', 'Receivable and Payable Accounts')
         ],
        string="Partner's",
        default='customer')
    partner_ids = fields.Many2many(
        'res.partner',
        string='Filter partners',
    )
    at_date = fields.Date(
        required=True,
        default=fields.Date.to_string(datetime.today()))
    until_date = fields.Date(
        "Clearance date", required=True,
        help="""The clearance date is essentially a tool used for debtors
        provisionning calculation.
        By default, this date is equal to the the end date (
        ie: 31/12/2011 if you select fy 2011).
        By amending the clearance date, you will be, for instance,
        able to answer the question : 'based on my last
        year end debtors open invoices, which invoices are still
        unpaid today (today is my clearance date)?'""")

    @api.onchange('at_date')
    def onchange_atdate(self):
        self.until_date = self.at_date

    @api.onchange('until_date')
    def onchange_untildate(self):
        # ---- until_date must be always >= of at_date
        if self.until_date:
            if self.until_date < self.at_date:
                raise UserError(
                    'Until Date must be equal or greater than At Date')

    @api.multi
    def check_report(self):
        return True
