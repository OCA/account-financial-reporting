from odoo import models


class CurrentStatementWizard(models.TransientModel):
    """Outstanding Statement wizard."""

    _name = "current.statement.wizard"
    _inherit = "statement.common.wizard"
    _description = "Current Statement Wizard"

    def _print_report(self, report_type):
        self.ensure_one()
        data = self._prepare_statement()
        if report_type == "xlsx":
            report_name = "p_s.report_current_statement_xlsx"
        else:
            report_name = "partner_statement.current_statement"
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
            .report_action(self, data=data)
        )

    def _export(self, report_type):
        """Default export is PDF."""
        return self._print_report(report_type)
