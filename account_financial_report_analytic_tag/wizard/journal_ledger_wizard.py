# Copyright 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class JournalLedgerReportWizard(models.TransientModel):
    _inherit = "journal.ledger.report.wizard"

    show_analytic_tags = fields.Boolean(
        default=True,
    )

    def _prepare_report_journal_ledger(self):
        res = super()._prepare_report_journal_ledger()
        res["show_analytic_tags"] = self.show_analytic_tags
        return res
