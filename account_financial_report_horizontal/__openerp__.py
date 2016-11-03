# -*- coding: utf-8 -*-
# © 2012-2016 Therp BV <http://therp.nl>
# © 2013 Agile Business Group sagl <http://www.agilebg.com>
# <lorenzo.battistini@agilebg.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Accounting Financial Reports Horizontal",
    "version": "9.0.0.0.0",
    "author": "Therp BV,Agile Business Group,Odoo Community Association (OCA)",
    "category": 'Accounting & Finance',
    'website': 'https://github.com/OCA/account-financial-reporting',
    'license': 'AGPL-3',
    "depends": ["account"],
    'data': [
        "data/report_paperformat.xml",
        "data/ir_actions_report_xml.xml",
        "report/report_financial.xml",
    ],
}
