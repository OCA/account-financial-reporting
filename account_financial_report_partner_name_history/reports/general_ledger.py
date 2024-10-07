#  Copyright 2024 Simone Rubino - Aion Tech
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class GeneralLedgerReport(models.AbstractModel):
    _inherit = "report.account_financial_report.general_ledger"

    def _get_report_values(self, docids, data):
        return super(
            GeneralLedgerReport,
            self.with_context(
                use_partner_name_history=True,
            ),
        )._get_report_values(docids, data)

    @api.model
    def _get_move_line_data(self, move_line):
        move_line_data = super()._get_move_line_data(move_line)
        # `partner_name` comes from the `display_name` used by `search_read`,
        # it is rightfully not affected by history name
        # because it is a stored field:
        # a value stored in database should not depend on
        # context or user that is seeing it.
        # That is why it has to be overwritten
        # with the move line's partner `name`.
        move_line = self.env["account.move.line"].browse(move_line_data["id"])
        move_line_data["partner_name"] = move_line.partner_id.name
        return move_line_data
