from openerp import models, api

class OpenInvoiceReport(models.AbstractModel):

    _name = 'report.account_financial_report_qweb.open_invoice_report_qweb'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        doc_ids = self._ids
        docargs = {
            'doc_model': 'account.move.line',
            'doc_ids': doc_ids,
            }
        if data:
            docargs.update(data)
        return report_obj.render(
            'account_financial_report_qweb.open_invoice_report_qweb',
            docargs)
