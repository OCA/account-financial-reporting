# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date
from openerp import api, fields, models


class CustomerOutstandingStatementWizard(models.TransientModel):
    """Customer Outstanding Statement wizard."""

    _name = 'customer.outstanding.statement.wizard'
    _description = 'Customer Outstanding Statement Wizard'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )

    date_end = fields.Date(required=True,
                           default=fields.Date.to_string(date.today()))
    show_aging_buckets = fields.Boolean(string='Include Aging Buckets',
                                        default=True)
    number_partner_ids = fields.Integer(
        default=lambda self: len(self._context['active_ids'])
    )
    filter_partners_non_due = fields.Boolean(
        string='Don\'t show partners with no due entries', default=True)

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        return self._export()

    def _prepare_outstanding_statement(self):
        self.ensure_one()
        return {
            'date_end': self.date_end,
            'company_id': self.company_id.id,
            'partner_ids': self._context['active_ids'],
            'show_aging_buckets': self.show_aging_buckets,
            'filter_non_due_partners': self.filter_partners_non_due,
        }

    def _export(self):
        """Export to PDF."""
        data = self._prepare_outstanding_statement()
        return self.env['report'].with_context(landscape=True).get_action(
            self, 'customer_outstanding_statement.statement', data=data)
