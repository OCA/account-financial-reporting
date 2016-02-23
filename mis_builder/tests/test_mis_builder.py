# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

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
        # create a report on a model without company_id field :
        # account.analytic.balance
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
                            'prefix': False,
                            'suffix': False,
                            'expr': 'len(test)',
                            'val_c': 'total_test = len(test)',
                            'val': 0,
                            'val_r': u'\u202f0\xa0',
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
