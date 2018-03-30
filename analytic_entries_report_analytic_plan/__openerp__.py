# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Analytic plans in analytic entries report",
    "version": "8.0.1.0.0",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "summary": "Group by analytic plans in analytic entries report",
    "depends": [
        'account_analytic_plans',
    ],
    "data": [
        "views/analytic_entries_report.xml",
    ],
    "external_dependencies": {
        'python': [
            'sqlparse',
        ],
    },
}
