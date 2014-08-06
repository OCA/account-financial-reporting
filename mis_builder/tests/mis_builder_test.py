#==============================================================================
#                                                                             =
#    mis_builder module for OpenERP, Management Information System Builder
#    Copyright (C) 2014 ACSONE SA/NV (<http://acsone.eu>)
#                                                                             =
#    This file is a part of mis_builder
#                                                                             =
#    mis_builder is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#                                                                             =
#    mis_builder is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#                                                                             =
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#                                                                             =
#==============================================================================

import openerp.tests.common as common
from openerp.addons.mis_builder import models
from collections import OrderedDict


DB = common.DB
ADMIN_USER_ID = common.ADMIN_USER_ID


class mis_builder_test(common.TransactionCase):

    def setUp(self):
        super(mis_builder_test, self).setUp()

    def test_datetime_conversion(self):
        date_to_convert = '2014-07-05'
        date_time_convert = models.mis_builder._utc_midnight(
            date_to_convert, 'Europe/Brussels')
        self.assertEqual(date_time_convert, '2014-07-04 22:00:00',
                         'The converted date time convert must contains hour')
        date_time_convert = models.mis_builder._utc_midnight(
            date_to_convert, 'Europe/Brussels', add_day=1)
        self.assertEqual(date_time_convert, '2014-07-05 22:00:00',
                         'The converted date time convert must contains hour')
        date_time_convert = models.mis_builder._utc_midnight(
            date_to_convert, 'US/Pacific')
        self.assertEqual(date_time_convert, '2014-07-05 07:00:00',
                         'The converted date time convert must contains hour')
        date_time_convert = models.mis_builder._utc_midnight(
            date_to_convert, 'US/Pacific', add_day=1)
        self.assertEqual(date_time_convert, '2014-07-06 07:00:00',
                         'The converted date time convert must contains hour')

    def test_fetch_query(self):
        # create a report on a model without company_id field :
        # account.analytic.balance
        data = self.registry('mis.report.instance').compute(
            self.cr, self.uid,
            self.ref('mis_builder.mis_report_instance_test'))
        self.assertDictContainsSubset(
            {'content':
             OrderedDict([(u'total_test',
                           {'kpi_name': u'total test',
                            'cols': [{'style': None,
                                      'val_c': None,
                                      'val': 0,
                                      'val_r': '0 '}]})]),
             'header': OrderedDict([('',
                                     {'kpi_name': '',
                                      'cols': [{'date': '2014-07-31',
                                                'name': u'today'}]
                                      })])
             }, data)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
