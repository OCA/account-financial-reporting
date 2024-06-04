# Copyright 2024 Akretion (https://www.akretion.com).
# @author Matthieu SAISON <matthieu.saison@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Account Financial Reports Start and End dates",
    "version": "14.0.1.0.0",
    "category": "Reporting",
    "summary": "OCA Financial Reports",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-reporting",
    "depends": [
        "account",
        "account_financial_report",
        "account_invoice_start_end_dates",
    ],
    "data": [
        "report/templates/general_ledger.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "AGPL-3",
}
