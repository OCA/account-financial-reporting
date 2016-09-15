# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Analytic plans in journal items",
    "version": "8.0.1.0.0",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "summary": "Show analytic plan in journal items analysis",
    "depends": [
        'account_analytic_plans',
    ],
    "data": [
        "views/account_entries_report.xml",
    ],
    "external_dependencies": {
        'python': [
            'sqlparse',
        ],
    },
}
