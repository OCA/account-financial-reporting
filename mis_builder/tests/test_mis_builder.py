# -*- coding: utf-8 -*-
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

import openerp.tests.common as common

from ..models import mis_builder


class TestMisBuilder(common.TransactionCase):

    def setUp(self):
        super(TestMisBuilder, self).setUp()

    def test_datetime_conversion(self):
        date_to_convert = '2014-07-05'
        date_time_convert = mis_builder._utc_midnight(
            date_to_convert, 'Europe/Brussels')
        self.assertEqual(date_time_convert, '2014-07-04 22:00:00',
                         'The converted date time convert must contains hour')
        date_time_convert = mis_builder._utc_midnight(
            date_to_convert, 'Europe/Brussels', add_day=1)
        self.assertEqual(date_time_convert, '2014-07-05 22:00:00',
                         'The converted date time convert must contains hour')
        date_time_convert = mis_builder._utc_midnight(
            date_to_convert, 'US/Pacific')
        self.assertEqual(date_time_convert, '2014-07-05 07:00:00',
                         'The converted date time convert must contains hour')
        date_time_convert = mis_builder._utc_midnight(
            date_to_convert, 'US/Pacific', add_day=1)
        self.assertEqual(date_time_convert, '2014-07-06 07:00:00',
                         'The converted date time convert must contains hour')

    def test_fetch_query(self):
        # create a report on account.analytic.line
        data = self.registry('mis.report.instance').compute(
            self.cr, self.uid,
            self.ref('mis_builder.mis_report_instance_test'))
        self.assertDictContainsSubset(
            {'content':
                [{'kpi_name': u'total test',
                  'default_style': False,
                  'cols': [{'period_id': self.ref('mis_builder.'
                                                  'mis_report_instance_'
                                                  'period_test'),
                            'style': None,
                            'suffix': False,
                            'expr': 'len(test)',
                            'val_c': 'total_test = len(test)',
                            'val': 0,
                            'val_r': u'0\xa0',
                            'is_percentage': False,
                            'dp': 0,
                            'drilldown': False}]
                  }],
             'header':
                 [{'kpi_name': '',
                   'cols': [{'date': '07/31/2014',
                             'name': u'today'}]
                   }],
             }, data)
