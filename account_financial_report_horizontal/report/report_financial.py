# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
from openerp import api, models


class ReportFinancial(models.AbstractModel):
    _inherit = 'report.account.report_financial'

    def get_account_lines(self, data, side=None):
        return super(
            ReportFinancial, self.with_context(
                account_financial_report_horizontal_side=side,
            )
        ).get_account_lines(data)

    def get_left_lines(self, data):
        return self.get_account_lines(data, side='left')

    def get_right_lines(self, data):
        return self.get_account_lines(data, side='right')

    @api.multi
    def render_html(self, data):
        data.setdefault('form', {}).update(
            get_left_lines=self.get_left_lines,
            get_right_lines=self.get_right_lines,
        )
        return super(ReportFinancial, self).render_html(data)
