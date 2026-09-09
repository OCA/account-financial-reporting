# Copyright 2019 Lorenzo Battistini @ TAKOBI
# Copyright 2025 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AbstractWizard(models.AbstractModel):
    _name = "account_financial_report_abstract_wizard"
    _description = "Abstract Wizard"

    def _get_partner_ids_domain(self):
        return [
            "&",
            "|",
            ("company_id", "=", self.company_id.id),
            ("company_id", "=", False),
            "|",
            ("parent_id", "=", False),
            ("is_company", "=", True),
        ]

    def _default_partners(self):
        context = self.env.context
        if context.get("active_ids") and context.get("active_model") == "res.partner":
            partners = self.env["res.partner"].browse(context["active_ids"])
            corp_partners = partners.filtered("parent_id")
            partners -= corp_partners
            partners |= corp_partners.mapped("commercial_partner_id")
            return partners.ids

    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
        required=False,
        string="Company",
    )
    # The column configuration is global per report, so this field is not
    # stored: it is resolved from `default_get()` on every access (including
    # cache misses while rendering the report). The dummy inverse only makes
    # the field writable, so that the inline list can propagate the user
    # changes to the `account.financial.report.column` records themselves.
    column_ids = fields.Many2many(
        comodel_name="account.financial.report.column",
        store=False,
        inverse=lambda self: self,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res["column_ids"] = (
            self.env["account.financial.report.column"]
            .search([("res_model", "=", self._name)])
            .ids
        )
        return res

    def button_export_html(self):
        self.ensure_one()
        report_type = "qweb-html"
        return self._export(report_type)

    def button_export_pdf(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def button_export_xlsx(self):
        self.ensure_one()
        report_type = "xlsx"
        return self._export(report_type)

    def _limit_text(self, value, limit=0):
        if value and limit and len(value) > limit:
            value = value[:limit] + "..."
        return value

    def _prepare_report_data(self):
        self.ensure_one()
        return {"wizard_name": self._name, "wizard_id": self.id}
