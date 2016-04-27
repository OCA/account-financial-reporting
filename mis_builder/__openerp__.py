# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'MIS Builder',
    'version': '8.0.1.0.0',
    'category': 'Reporting',
    'summary': """
        Build 'Management Information System' Reports and Dashboards
    """,
    'author': 'ACSONE SA/NV,'
              'Odoo Community Association (OCA)',
    'website': 'http://acsone.eu',
    'depends': [
        'account',
        'report_xls',  # OCA/reporting-engine
    ],
    'data': [
        'wizard/mis_builder_dashboard.xml',
        'views/mis_builder.xml',
        'security/ir.model.access.csv',
        'security/mis_builder_security.xml',
        'report/report_mis_report_instance.xml',
    ],
    'test': [
    ],
    'demo': [
        'tests/mis.report.kpi.csv',
        'tests/mis.report.query.csv',
        'tests/mis.report.csv',
        'tests/mis.report.instance.period.csv',
        'tests/mis.report.instance.csv',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
