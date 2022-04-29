# Copyright 2022 Moduon
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class JournalLedgerReportWizard(models.AbstractModel):
    _inherit = "account_financial_report_abstract_wizard"

    store_auto_sequence = fields.Boolean()
