# Copyright 2019 Lorenzo Battistini @ TAKOBI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AbstractWizard(models.AbstractModel):
    _name = 'account_financial_report_abstract_wizard'
    _description = 'Abstract Wizard'

    def _get_partner_ids_domain(self):
        return [
            '&',
            '|',
            ('company_id', '=', self.company_id.id),
            ('company_id', '=', False),
            '|',
            ('parent_id', '=', False),
            ('is_company', '=', True),
        ]

    def _default_partners(self):
        context = self.env.context
        if (
            context.get('active_ids') and
            context.get('active_model') == 'res.partner'
        ):
            partners = self.env['res.partner'].browse(context['active_ids'])
            corp_partners = partners.filtered('parent_id')
            partners -= corp_partners
            partners |= corp_partners.mapped('commercial_partner_id')
            return partners.ids
