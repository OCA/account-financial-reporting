# Copyright 2022 Moduon
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class JournalLedgerReport(models.AbstractModel):
    _inherit = "report.account_financial_report.journal_ledger"

    def _get_move_lines_data(self, ml, wizard, ml_taxes, auto_sequence, exigible):
        """Remember auto_sequence if required."""
        result = super()._get_move_lines_data(
            ml, wizard, ml_taxes, auto_sequence, exigible
        )
        if wizard.with_auto_sequence and wizard.store_auto_sequence:
            move = self.env["account.move"].browse(result["move_id"])
            move.legal_sequence = auto_sequence
        return result
