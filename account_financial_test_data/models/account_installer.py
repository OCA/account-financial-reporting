# -*- coding: utf-8 -*-
import logging
from openerp.osv import orm
from openerp import models, fields, api, _, exceptions

_logger = logging.getLogger(__name__)


class WizardMultiChartsAccounts(orm.TransientModel):
    """
    Execute wizard automatically without showing the wizard popup window
    """
    _inherit = 'wizard.multi.charts.accounts'

    def auto_execute(self, cr, uid, ids=False, context=None):
        if not context:
            context = {}
        context['lang'] = 'en_US'
        if not ids:
            ids = self.search(cr, uid, [], context=context)
        account_obj = self.pool.get('account.account')
        for wz in self.browse(cr, uid, ids, context=context):
            account_id = account_obj.search(
                cr,
                uid,
                [('company_id', '=', wz.company_id.id)],
                limit=1,
                context=context
            )
            if not account_id:
                # execute original wizard method
                _logger.info(
                    'Configure Accounting Data for Company: %s' %
                    wz.company_id.name
                )
                self.execute(cr, uid, [wz.id], context=context)


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
