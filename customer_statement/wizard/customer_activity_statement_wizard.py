# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date
from odoo import api, fields, models


class CustomerActivityStatementWizard(models.TransientModel):
    """Customer Activity Statement wizard."""

    _inherit = 'statement.common'
    _name = 'customer.activity.statement.wizard'
    _description = 'Customer Activity Statement Wizard'

    
    def _get_date_start(self):
        for record in self:
            record.date_start = fields.Date.context_today() - relativedelta(day=1)

    date_start = fields.Date(required=True, default='_get_date_start')
       
    account_type = fields.Selection(
        [('receivable', 'Receivable'),
         ('payable', 'Payable')], string='Account type', default='receivable')

    def _export(self):
        """Export to PDF."""
        data = self._prepare_statement()
        return self.env.ref(
            'customer_statement'
            '.action_print_customer_activity_statement').report_action(
            self, data=data)

    def _prepare_activity_statement(self):
        res = super()._prepare_activity_statement()
        res.update({'date_start': self.date_start})
        return res