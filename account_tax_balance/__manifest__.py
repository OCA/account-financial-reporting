# Copyright 2016 Lorenzo Battistini - Agile Business Group
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2016 ACSONE SA/NV - Stéphane Bidoul
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Tax Balance",
    "summary": "Compute tax balances based on date range",
    "version": "15.0.1.1.0",
    "development_status": "Mature",
    "category": "Invoices & Payments",
    "website": "https://github.com/OCA/account-financial-reporting",
    "author": "Agile Business Group, Therp BV, Tecnativa, ACSONE SA/NV, "
    "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["account", "date_range"],
    "data": [
        "wizard/open_tax_balances_view.xml",
        "views/account_move_view.xml",
        "views/account_tax_view.xml",
        "security/ir.model.access.csv",
    ],
    "images": ["images/tax_balance.png"],
    "pre_init_hook": "pre_init_hook",
}
