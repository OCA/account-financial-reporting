# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': "MIS Builder Analytic Axis Filter",
    'version': '8.0.1.0.0',
    'category': 'Reporting',
    'summary': """
        Add analytic filters to MIS Reports
    """,
    'author': 'ACSONE SA/NV,'
              'Odoo Community Association (OCA)',
    'website': "http://acsone.eu",
    'license': 'AGPL-3',
    'depends': [
        'mis_builder',
    ],
    'data': [
        'views/mis_report_view.xml',
        'views/mis_builder_analytic.xml',
    ],
    'qweb': [
        'static/src/xml/mis_widget.xml'
    ],
}
