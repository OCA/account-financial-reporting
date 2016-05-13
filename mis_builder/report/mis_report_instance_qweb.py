# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from openerp import api, models

_logger = logging.getLogger(__name__)


class Report(models.Model):
    _inherit = "report"

    @api.v7
    def get_pdf(self, cr, uid, ids, report_name, html=None, data=None,
                context=None):
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
