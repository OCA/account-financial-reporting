# -*- encoding: utf-8 -*-
##############################################################################
#
#    mis_builder module for Odoo, Management Information System Builder
#    Copyright (C) 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
#
#    This file is a part of mis_builder
#
#    mis_builder is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    mis_builder is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
        report = self._get_report_from_name(cr, uid, report_name)
        obj = self.pool[report.model].browse(cr, uid, ids,
                                             context=context)[0]
        context = context.copy()
        if hasattr(obj, 'landscape_pdf') and obj.landscape_pdf:
            context.update({'landscape': True})
        return super(Report, self).get_pdf(cr, uid, ids, report_name,
                                           html=html, data=data,
                                           context=context)
