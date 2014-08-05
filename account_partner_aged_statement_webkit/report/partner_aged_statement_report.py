# -*- encoding: utf-8 -*-

# ##############################################################################
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


import time
import operator
import itertools

from openerp import pooler
from openerp.osv import orm
from openerp.report import report_sxw
from openerp.tools.translate import _

from openerp.addons.account_financial_report_webkit.report.aged_partner_balance import (  # noqa
    AccountAgedTrialBalanceWebkit
)


class PartnerAgedStatementReport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(PartnerAgedStatementReport, self).__init__(cr, uid, name,
                                                         context=context)
        self.localcontext.update({
            'time': time,
        })


report_sxw.report_sxw(
    'report.webkit.partner_aged_statement_report',
    'account.account',
    ('addons/'
     'account_partner_aged_statement_webkit/'
     'report/'
     'partner_aged_statement.mako'),
    parser=PartnerAgedStatementReport)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
