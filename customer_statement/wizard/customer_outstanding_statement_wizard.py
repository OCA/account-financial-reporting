# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date
from odoo import api, fields, models


class CustomerOutstandingStatementWizard(models.TransientModel):
    """Customer Outstanding Statement wizard."""

    _name = 'customer.outstanding.statement.wizard'
    _description = 'Customer Outstanding Statement Wizard'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )

        def _export(self):
        """Export to PDF."""
        data = self._prepare_statement()
        return self.env.ref(
            'customer_statement'
            '.action_print_customer_outstanding_statement').report_action(
            self, data=data)
