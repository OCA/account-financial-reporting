# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    def init(self):
        res = super().init()
        self._cr.execute(
            """
            SELECT indexname FROM pg_indexes
            WHERE indexname = 'account_move_line_date_tax_line_id_idx'
        """
        )
        if not self._cr.fetchone():
            self._cr.execute(
                """
                CREATE INDEX account_move_line_date_tax_line_id_idx
                ON account_move_line (date, tax_line_id)
            """
            )
        return res
