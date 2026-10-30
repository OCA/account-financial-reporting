# Copyright 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AgedPartnerBalanceWizard(models.TransientModel):
    _inherit = "aged.partner.balance.report.wizard"

    show_analytic_tags = fields.Boolean(
        default=True,
        help="Show analytic tags on each move line "
        "(only visible when 'Show Move Line Details' is enabled).",
    )

    def _prepare_report_aged_partner_balance(self):
        res = super()._prepare_report_aged_partner_balance()
        res["show_analytic_tags"] = self.show_analytic_tags
        return res
