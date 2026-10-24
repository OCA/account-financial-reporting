# Copyright 2026 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AbstractWizard(models.AbstractModel):
    _inherit = "account_financial_report_abstract_wizard"

    more_company_ids = fields.Many2many(
        comodel_name="res.company",
        string="More Companies",
        domain="[('id', '!=', company_id)]",
    )

    @api.onchange("company_id")
    def _onchange_company_id_for_more(self):
        self.more_company_ids = False
