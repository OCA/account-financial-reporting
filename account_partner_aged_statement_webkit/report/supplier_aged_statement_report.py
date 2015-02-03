# -*- encoding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2010 - 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from .partner_aged_statement_report import PartnerAgedTrialReport
from openerp.report import report_sxw


class SupplierAgedTrialReport(PartnerAgedTrialReport):
    """
    This report is like partner_aged_statement_report but it returns only
    the amounts payable to the supplier
    """
    def __init__(self, cr, uid, name, context):
        super(SupplierAgedTrialReport, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'show_message': False,
        })
        self.ttype = 'payment'


report_sxw.report_sxw(
    'report.webkit.supplier_aged_statement_report',
    'res.partner',
    ('addons/'
     'account_partner_aged_statement_webkit/'
     'report/'
     'partner_aged_statement.mako'),
    parser=SupplierAgedTrialReport,
)
