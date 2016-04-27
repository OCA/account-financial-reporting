# -*- coding: utf-8 -*-
# Author: Andrea andrea4ever Gallina
# Author: Francesco OpenCode Apruzzese
# Author: Ciro CiroBoxHub Urselli
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError
from datetime import datetime


class OpenInvoiceWizard(models.TransientModel):

    _name = 'open.invoice.wizard'

    company_id = fields.Many2one(
        'res.company', required=True,
        default=lambda s: s.env.user.company_id)
    at_date = fields.Date(
        required=True,
        default=fields.Date.to_string(datetime.today()))
    partner_ids = fields.Many2many(
        'res.partner', comodel_name='res.partner',
        string='Filter partners',)
    amount_currency = fields.Boolean(
        "With Currency", help="It adds the currency column")
    group_by_currency = fields.Boolean(
        "Group Partner by currency", help="It adds the currency column")
    result_selection = fields.Selection([
        ('customer', 'Receivable Accounts'),
        ('supplier', 'Payable Accounts'),
        ('customer_supplier', 'Receivable and Payable Accounts')],
        "Partner's", required=True, default='customer')
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')], 'Target Moves',
        required=True, default='all')
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
                    'Until Date must be equal or greater then At Date')

    @api.multi
    def print_report(self):
        pass
