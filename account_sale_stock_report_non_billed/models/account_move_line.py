# Copyright 2022 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "account.move.line"

    def check_invoice_line_in_date(self, date_check, date_start=False):
        self.ensure_one()
        # Convert to the user time zone, as the raw datetime is stored in UTC and the
        # day could be shifted otherwise.
        line_date = (
            self.move_id.invoice_date
            or self.move_id.date
            or fields.Datetime.context_timestamp(self, self.create_date).date()
        )
        if date_start and line_date < date_start:
            return False
        return line_date <= date_check
