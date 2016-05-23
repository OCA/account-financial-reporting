# -*- coding: utf-8 -*-
# © 2016 Taktik
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from openerp import models, api

_logger = logging.getLogger(__name__)


class AccountAccountTemplate(models.Model):
    _inherit = "account.account.template"

    @api.model
    def generate_account(
            self,
            chart_template_id,
            tax_template_ref,
            acc_template_ref,
            code_digits,
            company_id):
        res = super(AccountAccountTemplate, self).generate_account(
            chart_template_id,
            tax_template_ref,
            acc_template_ref,
            code_digits,
            company_id
        )
        main_company_id = self.env['ir.model.data'].xmlid_to_res_id(
            'base.main_company'
        )
        if company_id == main_company_id:
            account_ids = []
            for template_account_id in res:
                account_ids.append(res[template_account_id])
        return res
