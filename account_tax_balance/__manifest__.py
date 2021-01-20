# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group
# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Tax Balance",
    "summary": "Compute tax balances based on date range",
    "version": "10.0.1.1.2",
    "category": "Accounting & Finance",
    "website": "https://www.agilebg.com/",
    "author": "Agile Business Group, Therp BV, Tecnativa, ACSONE SA/NV, "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account",
        "date_range",
    ],
    "data": [
        "wizard/open_tax_balances_view.xml",
        "views/account_move_view.xml",
        "views/account_tax_view.xml",
    ],
    "images": [
        'images/tax_balance.png',
    ]
}
