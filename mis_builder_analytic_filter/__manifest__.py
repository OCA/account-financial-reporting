# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Mis Builder Analytic Filter',
    'summary': """
        Add analytic filters to MIS Reports""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,Odoo Community Association (OCA)',
    'website': 'http://acsone.eu',
    'depends': [
        'mis_builder',
    ],
    'data': [
        'views/mis_report_instance.xml',
        'views/mis_report_analytic_filter.xml'
    ],
    'qweb': [
        'static/src/xml/mis_widget.xml'
    ],
}
