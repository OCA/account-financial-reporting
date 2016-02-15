# -*- coding: utf-8 -*-
# © 2015 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Analytic Entries Statistics per fiscal period or year",
    "version": "8.0.1.0.1",
    "license": "AGPL-3",
    "author": "Odoo Community Association (OCA),Therp BV",
    "website": "https://github.com/OCA/account-financial-reporting",
    "category": "Accounting & Finance",
    "depends": [
        'account',
    ],
    "data": [
        "views/analytics_entry_report.xml",
    ],
    "external_dependencies": {
        'python': [
            'sqlparse',
        ],
    },
}
