# Copyright 2022 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models


class StockMove(models.Model):
    _inherit = "account.move.line"

    def check_invoice_line_in_date(self, date_check, date_start=False):
        self.ensure_one()
        start = True
        if date_start:
            start = (
                self.move_id.invoice_date
                or self.move_id.date
                or self.create_date.date()
            ) >= date_start
        return (
            start
            and (
                self.move_id.invoice_date
                or self.move_id.date
                or self.create_date.date()
            )
            <= date_check
        )
