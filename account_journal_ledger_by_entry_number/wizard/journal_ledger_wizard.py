from odoo import _, api, fields, models


class JournalLedgerReportWizard(models.TransientModel):
    _inherit = "journal.ledger.report.wizard"

    sort_option = fields.Selection(default="entry_number")

    @api.model
    def _get_sort_options(self):
        return [("entry_number", _("Entry number")), ("date", _("Date"))]
