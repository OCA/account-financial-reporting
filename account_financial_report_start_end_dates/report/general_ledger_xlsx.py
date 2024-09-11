from odoo import _, models


class GeneralLedgerXslx(models.AbstractModel):
    _inherit = "report.a_f_r.report_general_ledger_xlsx"

    def _get_report_columns(self, report):
        res = super()._get_report_columns(report)
        ures = {}
        deb_found = 0
        for k, v in res.items():
            if not deb_found:
                ures.update({k: v})
            if v["header"] == _("Debit"):
                deb_found = 1
                ures.update(
                    {k: {"header": _("Start Date"), "field": "start_date", "width": 15}}
                )
                ures.update(
                    {k + 1: {"header": _("End Date"), "field": "end_date", "width": 15}}
                )
            if deb_found:
                ures.update({k + 2: v})
        return ures
