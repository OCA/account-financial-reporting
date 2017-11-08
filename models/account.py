# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    compacted = fields.Boolean('Compacte reconciled entries.', help='If flagged, no details will be displayed in the Standard report, only compacted amounts per period.', default=False)
    type_third_parties = fields.Selection([('no', 'No'), ('supplier', 'Supplier'), ('customer', 'Customer')], string='Third Partie', required=True, default='no')
