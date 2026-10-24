# Copyright 2026 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

ALLOW_REPORTS = [
    "general.ledger.report.wizard",
    "journal.ledger.report.wizard",
    "trial.balance.report.wizard",
    "open.items.report.wizard",
    "aged.partner.balance.report.wizard",
    "vat.report.wizard",
]


class AbstractReportXslx(models.AbstractModel):
    _inherit = "report.account_financial_report.abstract_report_xlsx"

    def generate_xlsx_report(self, workbook, data, objects):
        # For multi-company reports, generate one sheet per selected company
        if data.get("context", {}).get("active_model") in ALLOW_REPORTS:
            company_ids = objects.company_id + objects.more_company_ids
            for company_id in company_ids:
                res = self.with_company(company_id)._generate_xlsx_report_company(
                    workbook, dict(data, company_id=company_id.id), objects
                )
        else:
            res = self._generate_xlsx_report_company(workbook, data, objects)
        return res

    def _generate_xlsx_report_company(self, workbook, data, objects):
        return super().generate_xlsx_report(workbook, data, objects)
