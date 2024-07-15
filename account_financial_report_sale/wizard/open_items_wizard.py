# Copyright 2024 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class OpenItemsReportWizard(models.TransientModel):

    _inherit = "open.items.report.wizard"

    grouped_by = fields.Selection(
        selection_add=[("partner_shipping", "Delivery Address")]
    )
