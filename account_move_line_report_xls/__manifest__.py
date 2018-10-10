# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Move Line XLSX export',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': "Noviat, Odoo Community Association (OCA)",
    'category': 'Accounting & Finance',
    'summary': 'Journal Items Excel export',
    'depends': ['account', 'report_xlsx_helper'],
    'data': [
        'report/move_line_list_xls.xml',
    ],
    'installable': True,
}
