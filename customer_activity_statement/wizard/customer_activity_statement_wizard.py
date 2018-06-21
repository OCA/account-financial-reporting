# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date
from odoo import api, fields, models


class CustomerActivityStatementWizard(models.TransientModel):
    """Customer Activity Statement wizard."""

    _name = 'customer.activity.statement.wizard'
    _description = 'Customer Activity Statement Wizard'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )

    date_start = fields.Date(required=True,
                             default=fields.Date.to_string(
                                 date(date.today().year, 1, 1)))
    date_end = fields.Date(required=True,
                           default=fields.Date.to_string(date.today()))
    show_aging_buckets = fields.Boolean(string='Include Aging Buckets',
                                        default=True)
    number_partner_ids = fields.Integer(
        default=lambda self: len(self._context['active_ids'])
    )
    filter_partners_non_due = fields.Boolean(
        string='Don\'t show partners with no due entries', default=True)
    account_type = fields.Selection(
        [('receivable', 'Receivable'),
         ('payable', 'Payable')], string='Account type', default='receivable')

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        return self._export()

    def _prepare_activity_statement(self):
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
        """Export to PDF."""
        data = self._prepare_activity_statement()
        return self.env.ref(
            'customer_activity_statement'
            '.action_print_customer_activity_statement').report_action(
            self, data=data)
