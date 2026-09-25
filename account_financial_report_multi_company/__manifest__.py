# Copyright 2026 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Financial Reports - Multi Company",
    "summary": "Add muti company support for financial reports",
    "version": "18.0.1.0.0",
    "category": "Reporting",
    "license": "AGPL-3",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-reporting",
    "depends": ["account_financial_report"],
    "data": [
        "wizard/general_ledger_wizard_view.xml",
        "wizard/journal_ledger_wizard_view.xml",
        "wizard/trial_balance_wizard_view.xml",
        "wizard/open_items_wizard_view.xml",
        "wizard/aged_partner_balance_wizard_view.xml",
        "wizard/vat_report_wizard_view.xml",
    ],
    "maintainers": ["kittiu", "Saran440"],
    "installable": True,
}
