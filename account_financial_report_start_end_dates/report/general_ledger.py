# Copyright 2024 Akretion (https://www.akretion.com).
# @author Matthieu SAISON <matthieu.saison@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class GeneralLedgerReport(models.AbstractModel):
    _inherit = "report.account_financial_report.general_ledger"

    @api.model
    def _get_move_line_data(self, move_line):
        move_line_data = super()._get_move_line_data(move_line)
        move_line_data.update(
            {
                "start_date": move_line["start_date"],
                "end_date": move_line["end_date"],
            }
        )

        return move_line_data

    @api.model
    def _calculate_centralization(self, centralized_ml, move_line, date_to):
        centralized_ml = super()._calculate_centralization(
            centralized_ml, move_line, date_to
        )
        jnl_id = move_line["journal_id"]
        month = move_line["date"].month
        for jnl_id in centralized_ml:
            for month in centralized_ml[jnl_id]:
                centralized_ml[jnl_id][month] |= {
                    "start_date": False,
                    "end_date": False,
                }
        return centralized_ml

    def _get_ml_fields(self):
        ml_fields = super()._get_ml_fields()
        res = ml_fields + [
            "start_date",
            "end_date",
        ]
        return res
