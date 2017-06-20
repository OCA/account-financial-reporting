# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Mis Builder Budget',
    'summary': """
        Create budgets for MIS reports""",
    'version': '8.0.1.0.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,Noviat,Odoo Community Association (OCA)',
    'depends': [
        'mis_builder',
    ],
    'data': [
        'views/mis_report.xml',
        'views/mis_report_instance.xml',
        'security/mis_budget_item.xml',
        'views/mis_budget_item.xml',
        'security/mis_budget.xml',
        'views/mis_budget.xml',
    ],
    'demo': [
        'demo/mis_report.xml',
        'demo/mis_budget.xml',
        'demo/mis_report_instance.xml',
    ],
    'installable': True,
    'application': True,
}
