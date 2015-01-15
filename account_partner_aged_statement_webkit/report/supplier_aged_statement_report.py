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
from dateutil.relativedelta import relativedelta
from openerp import pooler
from datetime import datetime


class SupplierAgedTrialReport(PartnerAgedTrialReport):
    """
    This report is like partner_aged_statement_report but it returns only
    the amounts payable to the supplier
    """
    def __init__(self, cr, uid, name, context):
        super(SupplierAgedTrialReport, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'getLines30': self._lines_get30,
            'getLines3060': self._lines_get_30_60,
            'getLines60': self._lines_get60,
            'show_message': False,
        })

    def _lines_get30(self, obj):
        today = datetime.now()
        stop = today - relativedelta(days=30)

        moveline_obj = pooler.get_pool(self.cr.dbname)['account.move.line']
        movelines = moveline_obj.search(
            self.cr, self.uid,
            [('partner_id', '=', obj.id),
             ('account_id.type', 'in', ['payable']),
             ('state', '<>', 'draft'), ('reconcile_id', '=', False),
             '|',
             '&', ('date_maturity', '<=', today), ('date_maturity', '>', stop),
             '&', ('date_maturity', '=', False),
             '&', ('date', '<=', today), ('date', '>', stop)],
            context=self.localcontext)
        movelines = moveline_obj.browse(self.cr, self.uid, movelines)
        return movelines

    def _lines_get_30_60(self, obj):
        start = datetime.now() - relativedelta(days=30)
        stop = start - relativedelta(days=30)

        moveline_obj = pooler.get_pool(self.cr.dbname)['account.move.line']
        movelines = moveline_obj.search(
            self.cr, self.uid,
            [('partner_id', '=', obj.id),
             ('account_id.type', 'in', ['payable']),
             ('state', '<>', 'draft'), ('reconcile_id', '=', False),
             '|',
             '&', ('date_maturity', '<=', start), ('date_maturity', '>', stop),
             '&', ('date_maturity', '=', False),
             '&', ('date', '<=', start), ('date', '>', stop)],
            context=self.localcontext)
        movelines = moveline_obj.browse(self.cr, self.uid, movelines)
        return movelines

    def _lines_get60(self, obj):
        start = datetime.now() - relativedelta(days=60)

        moveline_obj = pooler.get_pool(self.cr.dbname)['account.move.line']
        movelines = moveline_obj.search(
            self.cr, self.uid,
            [('partner_id', '=', obj.id),
             ('account_id.type', 'in', ['payable']),
             ('state', '<>', 'draft'), ('reconcile_id', '=', False),
             '|', ('date_maturity', '<=', start),
             ('date_maturity', '=', False), ('date', '<=', start)],
            context=self.localcontext)
        movelines = moveline_obj.browse(self.cr, self.uid, movelines)
        return movelines

report_sxw.report_sxw(
    'report.webkit.supplier_aged_statement_report',
    'res.partner',
    ('addons/'
     'account_partner_aged_statement_webkit/'
     'report/'
     'partner_aged_statement.mako'),
    parser=SupplierAgedTrialReport,
)
