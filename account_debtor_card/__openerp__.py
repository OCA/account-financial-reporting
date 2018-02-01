# -*- coding: utf-8 -*-
# © 2018 Sunflower IT (http://sunflowerweb.nl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Debtor Card",
    "summary": "Adds an option to print sale orders and related invoices",
    "version": "8.0.1.0.0",
    "category": "Accounting",
    "website": "https://sunflowerweb.nl",
    "author": "Sunflower IT, Therp BV, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "sale",
        "account",
    ],
    "data": [
        "views/res_partner.xml",
        "report/report_debtor_card.xml",
    ],
}
