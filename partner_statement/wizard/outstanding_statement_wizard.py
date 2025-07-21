# Copyright 2018 ForgeFlow, S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models
from datetime import date


class OutstandingStatementWizard(models.TransientModel):
    """Outstanding Statement wizard."""

    _name = "outstanding.statement.wizard"
    _inherit = "statement.common.wizard"
    _description = "Outstanding Statement Wizard"

    def _prepare_statement(self):
        res = super()._prepare_statement()
        res.update(
            {
                "is_outstanding": True,
            }
        )
        ctx = self.env.context.copy()
        if ctx.get("from_menu", False):
            import ipdb;ipdb.set_trace()

            partner_domain = [('invoice_date_due', '<', date.today().isoformat()),('state', '=', 'posted'),('payment_state', 'in', ('not_paid', 'partial')),]
            if self.account_type == 'asset_receivable':
                partner_domain.append(('move_type', 'in', ('out_invoice', 'out_refund')))
            if self.account_type == 'liability_payable':
                partner_domain.append(('move_type', 'in', ('in_invoice', 'in_refund')))
            partners = self.env['account.move'].search(partner_domain, limit=3).mapped('partner_id')
            res["partner_ids"] = partners.ids

        return res

    def _print_report(self, report_type):
        self.ensure_one()
        data = self._prepare_statement()
        if report_type == "xlsx":
            report_name = "p_s.report_outstanding_statement_xlsx"
        else:
            report_name = "partner_statement.outstanding_statement"
        partners = self.env["res.partner"].browse(data["partner_ids"])
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
            .report_action(partners, data=data)
        )

    def _export(self, report_type):
        """Default export is PDF."""
        return self._print_report(report_type)
