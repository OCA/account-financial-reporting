# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models
from openerp.addons.account.report.report_vat import tax_report
from functools import partial


class TaxReport(tax_report):
    def __init__(self, cr, uid, name, context=None):
        super(TaxReport, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_lines': partial(self._get_lines, context=context),
        })

    def _get_lines(self, based_on, company_id=False, parent=False, level=0,
                   context=None):
        result = super(TaxReport, self)._get_lines(
            based_on, company_id=company_id, parent=parent, level=level,
            context=context)
        return filter(lambda x: x['tax_amount'], result)


class ReportVat(models.AbstractModel):
    _inherit = 'report.account.report_vat'
    _wrapped_report_class = TaxReport
