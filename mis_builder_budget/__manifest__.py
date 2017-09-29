# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Mis Builder Budget',
    'summary': """
        Create budgets for MIS reports""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-reporting/',
    'depends': [
        'mis_builder',
    ],
    'data': [
        'views/mis_report_instance_period.xml',
        'views/mis_report.xml',
        'security/mis_budget_item.xml',
        'views/mis_budget_item.xml',
        'security/mis_budget.xml',
        'views/mis_budget.xml',
    ],
    'demo': [
    ],
}
