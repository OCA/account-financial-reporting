# © 2023 FactorLibre - Alejandro Ji Cheung <alejandro.jicheung@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class JournalLedgerReport(models.AbstractModel):
    _inherit = "report.account_financial_report.journal_ledger"

    def _get_moves_data(self, move):
        res = super()._get_moves_data(move)
        if res.get("entry", False) and move.entry_number:
            res["entry"] = move.entry_number
        return res

    def _get_moves_order(self, wizard, journal_ids):
        res = super()._get_moves_order(wizard, journal_ids)
        if wizard.sort_option == "entry_number" and res == "":
            return "entry_number asc"
        return res
