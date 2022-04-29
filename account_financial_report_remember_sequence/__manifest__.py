# Copyright 2022 Moduon
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Remember automatic financial report legal sequence",
    "summary": "Allow accountant to remember last legal sequence number",
    "version": "15.0.1.0.0",
    "development_status": "Beta",
    "category": "OCA Financial Reports",
    "website": "https://github.com/OCA/account-financial-reporting",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["Yajo"],
    "license": "AGPL-3",
    "depends": [
        "account_financial_report",
    ],
    "data": [
        "views/account_move.xml",
        "wizards/journal_ledger_wizard.xml",
    ],
}
