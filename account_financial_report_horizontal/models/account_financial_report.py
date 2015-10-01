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
from openerp import models, api


class AccountFinancialReport(models.Model):
    _inherit = 'account.financial.report'

    @api.multi
    def _has_exclusively_report_types(self, report_types):
        self.ensure_one()
        if self.type == 'accounts':
            for account in self.account_ids:
                if account.user_type.report_type not in report_types:
                    return False
        elif self.type == 'account_type':
            for account_type in self.account_type_ids:
                if account_type.report_type not in report_types:
                    return False
        elif self.type == 'account_report':
            # this will have mixed types usually, we rely upon this being
            # filtered out by siblings of this report
            return True
        return all(
            r._has_exclusively_report_types(report_types)
            for r in self.children_ids)

    @api.multi
    def _get_children_by_order(self):
        reports = super(AccountFinancialReport, self)._get_children_by_order()
        if self.env.context.get('account_financial_report_horizontal_side'):
            side = self.env.context['account_financial_report_horizontal_side']
            report_types = {
                'left': ['income', 'asset', 'none'],
                'right': ['expense', 'liability', 'none']
            }[side]
            last_good_report = None
            last_bad_report = None
            for report in self.browse(reports):
                if not report.parent_id:
                    yield report.id
                # don't check children if we already checked the parent
                elif report.parent_id == last_bad_report:
                    continue
                elif report.parent_id == last_good_report\
                        or report._has_exclusively_report_types(report_types):
                    last_good_report = report
                    yield report.id
                else:
                    last_bad_report = report
        else:
            for report_id in reports:
                yield report_id
