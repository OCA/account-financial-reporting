# Copyright 2022 Moduon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    legal_sequence = fields.Integer(
        index=True,
        readonly=True,
        help="Legal numeric sequence stored last time the report was generated.",
    )
