# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'MIS Builder',
    'version': '9.0.2.0.2',
    'category': 'Reporting',
    'summary': """
        Build 'Management Information System' Reports and Dashboards
    """,
    'author': 'ACSONE SA/NV,'
              'Odoo Community Association (OCA)',
    'website': 'http://acsone.eu',
    'depends': [
        'account',
        'report_xlsx',  # OCA/reporting-engine
        'date_range',  # OCA/server-tools
        'web_widget_color',  # OCA/web
    ],
    'data': [
        'wizard/mis_builder_dashboard.xml',
        'views/mis_report.xml',
        'views/mis_report_instance.xml',
        'views/mis_report_style.xml',
        'datas/ir_cron.xml',
        'security/ir.model.access.csv',
        'security/mis_builder_security.xml',
        'report/mis_report_instance_qweb.xml',
        'report/mis_report_instance_xlsx.xml',
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
    'license': 'AGPL-3',
}
