# Copyright 2013 Camptocamp SA
# Copyright 2017 ACSONE SA/NV
# Copyright 2017 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Export CSV",
    "summary": "Adds accounting CSV export",
    "version": "14.0.0.0.1",
    "depends": [
        "account",
        "date_range",
    ],
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-reporting",
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "wizard/account_export_csv_view.xml",
    ],
    "installable": True,
}
