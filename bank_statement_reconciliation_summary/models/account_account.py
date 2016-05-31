# -*- coding: utf-8 -*-
# © 2016 Eficent Business and IT Consulting Services S.L.
# © 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    clearing_account_id = fields.Many2one('account.account',
                                          'Clearing Account')
