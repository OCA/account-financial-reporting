# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Customer Activity Statement',
    'version': '10.0.1.1.0',
    'category': 'Accounting & Finance',
    'summary': 'OCA Financial Reports',
    'author': "Eficent, Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/account-financial-reporting',
    'license': 'AGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'views/statement.xml',
        'wizard/customer_activity_statement_wizard.xml',
    ],
    'installable': True,
    'application': False,
}
