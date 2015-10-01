# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2015 Therp BV (<http://therp.nl>).
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
##############################################################################
import copy
from openerp import models
from openerp.addons.account.report.account_financial_report import\
    report_account_common


class report_account_common_horizontal(report_account_common):
    def __init__(self, cr, uid, name, context=None):
        super(report_account_common_horizontal, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_left_lines': self.get_left_lines,
            'get_right_lines': self.get_right_lines,
        })

    def get_lines(self, data, side=None):
        data = copy.deepcopy(data)
        if data['form']['used_context'] is None:
            data['form']['used_context'] = {}
        data['form']['used_context'].update(
            account_financial_report_horizontal_side=side)
        return super(report_account_common_horizontal, self).get_lines(
            data)

    def get_left_lines(self, data):
        return self.get_lines(data, side='left')

    def get_right_lines(self, data):
        return self.get_lines(data, side='right')


class ReportFinancial(models.AbstractModel):
    _inherit = 'report.account.report_financial'
    _wrapped_report_class = report_account_common_horizontal
