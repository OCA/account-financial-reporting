# Copyright 2019 ADHOC SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountAccount(models.Model):

    _inherit = "account.account"

    hide_in_cash_flow = fields.Boolean(string="Hide in Cash Flow?")
