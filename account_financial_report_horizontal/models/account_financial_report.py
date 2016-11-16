# -*- coding: utf-8 -*-
# © 2015 Therp BV <http://therp.nl>
from openerp import models, api


class AccountFinancialReport(models.Model):
    _inherit = 'account.financial.report'

    @api.multi
    def _has_exclusively_report_types(self, report_types):
        self.ensure_one()
        if self.type == 'accounts':
            for account in self.account_ids:
                if account.user_type_id.type not in report_types:
                    return False
        elif self.type == 'account_type':
            for account_type in self.account_type_ids:
                if account_type.type not in report_types:
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
                'left': ['receivable', 'liquidity', 'other'],
                'right': ['payable', 'other']
            }[side]
            last_good_report = self.browse([])
            last_bad_report = self.browse([])
            result = self.browse([])
            for report in reports:
                if not report.parent_id:
                    result += report
                # don't check children if we already checked the parent
                elif report.parent_id == last_bad_report:
                    continue
                elif report.parent_id == last_good_report\
                        or report._has_exclusively_report_types(report_types):
                    last_good_report = report
                    result += report
                else:
                    last_bad_report = report
            return result
        else:
            return reports
