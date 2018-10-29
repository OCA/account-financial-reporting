# -*- coding: utf-8 -*-
# Copyright 2018 Graeme Gellatly
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class StatementCommon(models.AbstractModel):

    _name = 'statement.common'

    name = fields.Char()
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )
    date_end = fields.Date(required=True,
                           default=fields.Date.context_today)
    show_aging_buckets = fields.Selection(
        [('auto', 'Auto'), ('always', 'Always'), ('never', 'Never')], 
        string='Include Aging Buckets', default=True)
    number_partner_ids = fields.Integer(
        default=lambda self: len(self._context['active_ids'])
    )
    filter_partners_non_due = fields.Boolean(
        string='Don\'t show partners with no due entries', default=True)

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        return self._export()

    def _prepare_statement(self):
        self.ensure_one()
        return {
            'date_start': self.date_start,
            'date_end': self.date_end,
            'company_id': self.company_id.id,
            'partner_ids': self._context['active_ids'],
            'show_aging_buckets': self.show_aging_buckets,
            'filter_non_due_partners': self.filter_partners_non_due,
            'account_type': self.account_type,
        }

    def _export(self):
        raise NotImplementedError
