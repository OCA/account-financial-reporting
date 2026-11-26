# Copyright 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Account Financial Reports - Analytic Tags",
    "version": "18.0.1.0.0",
    "category": "Reporting",
    "summary": "Adds an Analytic Tags column to the OCA financial reports",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-reporting",
    "depends": ["account_financial_report", "account_analytic_tag"],
    "data": [
        "wizard/general_ledger_wizard_view.xml",
        "wizard/journal_ledger_wizard_view.xml",
        "wizard/open_items_wizard_view.xml",
        "wizard/aged_partner_balance_wizard_view.xml",
        "report/templates/general_ledger.xml",
        "report/templates/journal_ledger.xml",
        "report/templates/open_items.xml",
        "report/templates/aged_partner_balance.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
}
