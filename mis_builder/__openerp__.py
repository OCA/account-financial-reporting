# -*- encoding: utf-8 -*-
##############################################################################
#
#    mis_builder module for Odoo, Management Information System Builder
#    Copyright (C) 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
#
#    This file is a part of mis_builder
#
#    mis_builder is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    mis_builder is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'MIS Builder',
    'version': '0.1',
    'category': 'Reporting',
    'summary': """
        Build 'Management Information System' Reports and Dashboards
    """,
    'author': 'ACSONE SA/NV',
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
        # 'report/report_mis_report_instance.xml',
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
    'js': [
        'static/src/js/*.js'
    ],
    'css': [
        'static/src/css/*.css'
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
