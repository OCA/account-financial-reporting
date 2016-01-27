# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from openerp import api, models

_logger = logging.getLogger(__name__)


class ReportMisReportInstance(models.AbstractModel):

    _name = 'report.mis_builder.report_mis_report_instance'

    @api.multi
    def render_html(self, data=None):
        docs = self.env['mis.report.instance'].browse(self._ids)
        docs_computed = {}
        for doc in docs:
            docs_computed[doc.id] = doc.compute()
        docargs = {
            'doc_ids': self._ids,
            'doc_model': 'mis.report.instance',
            'docs': docs,
            'docs_computed': docs_computed,
        }
        return self.env['report'].\
            render('mis_builder.report_mis_report_instance', docargs)


class Report(models.Model):
    _inherit = "report"

    @api.v7
    def get_pdf(self, cr, uid, ids, report_name, html=None, data=None,
                context=None):
        if not ids and context.get('active_ids') and\
                report_name == 'mis_builder.report_mis_report_instance':
            ids = context.get('active_ids')
        if ids:
            report = self._get_report_from_name(cr, uid, report_name)
            obj = self.pool[report.model].browse(cr, uid, ids,
                                                 context=context)[0]
            context = context.copy()
            if hasattr(obj, 'landscape_pdf') and obj.landscape_pdf:
                context.update({'landscape': True})
        return super(Report, self).get_pdf(cr, uid, ids, report_name,
                                           html=html, data=data,
                                           context=context)
