# -*- coding: utf-8 -*-
# © 2011 Guewen Baconnier (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).-
from openerp import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    centralized = fields.Boolean(
        'Centralized',
        default=False,
        help="If flagged, no details will be displayed in "
             "the General Ledger report (the webkit one only), "
             "only centralized amounts per period.")
