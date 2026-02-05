# Copyright 2018 Graeme Gellatly
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.osv import expression


class StatementCommon(models.AbstractModel):
    _name = "statement.common.wizard"
    _description = "Statement Reports Common Wizard"

    name = fields.Char()
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        string="Company",
        required=True,
    )
    date_end = fields.Date(required=True, default=fields.Date.context_today)
    show_aging_buckets = fields.Boolean(default=True)
    show_only_overdue = fields.Boolean(
        help="Show only lines due before the selected date",
    )
    number_partner_ids = fields.Integer(
        default=lambda self: len(self._context.get("active_ids", []))
    )
    filter_partners_non_due = fields.Boolean(
        string="Don't show partners with no due entries", default=True
    )
    filter_negative_balances = fields.Boolean("Exclude Negative Balances", default=True)

    aging_type = fields.Selection(
        [("days", "Age by Days"), ("months", "Age by Months")],
        string="Aging Method",
        default="days",
        required=True,
    )

    account_type = fields.Selection(
        [("asset_receivable", "Receivable"), ("liability_payable", "Payable")],
        default="asset_receivable",
    )
    excluded_accounts_selector = fields.Char(
        string="Accounts to exclude",
        help="Select account codes to be excluded "
        "with a comma-separated list of expressions like 70%.",
    )

    @api.model
    def _get_excluded_accounts_domain(self, selector):
        """Convert an account codes selector to a domain to search accounts.

        The selector is a comma-separated list of expressions like 70%.
        The algorithm is the same as
        AccountingExpressionProcessor._account_codes_to_domain
        of `mis_builder` module.
        """
        if not selector:
            selector = ""
        domains = []
        for account_code in selector.split(","):
            account_code = account_code.strip()
            if "%" in account_code:
                domains.append(
                    [
                        ("code", "=like", account_code),
                    ]
                )
            else:
                domains.append(
                    [
                        ("code", "=", account_code),
                    ]
                )
        return expression.OR(domains)

    def _get_excluded_accounts(self):
        self.ensure_one()
        domain = self._get_excluded_accounts_domain(self.excluded_accounts_selector)
        return self.env["account.account"].search(domain)

    @api.onchange("aging_type")
    def onchange_aging_type(self):
        if self.aging_type == "months":
            self.date_end = fields.Date.context_today(self).replace(
                day=1
            ) - relativedelta(days=1)
        else:
            self.date_end = fields.Date.context_today(self)

    def _prepare_statement(self):
        self.ensure_one()
        return {
            "date_end": self.date_end,
            "company_id": self.company_id.id,
            "partner_ids": self._context["active_ids"],
            "show_aging_buckets": self.show_aging_buckets,
            "show_only_overdue": self.show_only_overdue,
            "filter_non_due_partners": self.filter_partners_non_due,
            "account_type": self.account_type,
            "aging_type": self.aging_type,
            "filter_negative_balances": self.filter_negative_balances,
            "excluded_accounts_ids": self._get_excluded_accounts().ids,
        }

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
