# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# Copyright 2018 Jacques-Etienne Baudoux (BCIM sprl) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Add XLSX export to accounting reports',
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': "BCIM,Noviat,Odoo Community Association (OCA)",
    'category': 'Generic Modules/Accounting',
    'depends': ['report_xlsx', 'account_financial_report_webkit_xls'],
    'data': [
        'report/general_ledger.xml',
    ],
    'installable': True,
}
