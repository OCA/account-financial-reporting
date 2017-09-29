# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import odoo.tests.common as common

from ..models.mis_report_instance import (
    MODE_NONE, MODE_FIX, MODE_REL,
    SRC_SUMCOL,
    DateFilterRequired, DateFilterForbidden,
)


class TestPeriodDates(common.TransactionCase):

    def setUp(self):
        super(TestPeriodDates, self).setUp()
        self.report_obj = self.env['mis.report']
        self.instance_obj = self.env['mis.report.instance']
        self.period_obj = self.env['mis.report.instance.period']
        self.report = self.report_obj.create(dict(
            name='test-report',
        ))
        self.instance = self.instance_obj.create(dict(
            name='test-instance',
            report_id=self.report.id,
            comparison_mode=False,
        ))
        self.assertEqual(len(self.instance.period_ids), 1)
        self.period = self.instance.period_ids[0]

    def test_date_filter_constraints(self):
        self.instance.comparison_mode = True
        with self.assertRaises(DateFilterRequired):
            self.period.write(dict(
                mode=MODE_NONE,
            ))
        with self.assertRaises(DateFilterForbidden):
            self.period.write(dict(
                mode=MODE_FIX,
                source=SRC_SUMCOL,
            ))

    def test_simple_mode(self):
        # not comparison_mode
        self.assertFalse(self.instance.comparison_mode)
        period = self.instance.period_ids[0]
        self.assertEqual(period.date_from, self.instance.date_from)
        self.assertEqual(period.date_to, self.instance.date_to)

    def tests_mode_none(self):
        self.instance.comparison_mode = True
        self.period.write(dict(
            mode=MODE_NONE,
            source=SRC_SUMCOL,
        ))
        self.assertFalse(self.period.date_from)
        self.assertFalse(self.period.date_to)
        self.assertTrue(self.period.valid)

    def tests_mode_fix(self):
        self.instance.comparison_mode = True
        self.period.write(dict(
            mode=MODE_FIX,
            manual_date_from='2017-01-01',
            manual_date_to='2017-12-31',
        ))
        self.assertEqual(self.period.date_from, '2017-01-01')
        self.assertEqual(self.period.date_to, '2017-12-31')
        self.assertTrue(self.period.valid)

    def test_rel_day(self):
        self.instance.write(dict(
            comparison_mode=True,
            date='2017-01-01'
        ))
        self.period.write(dict(
            mode=MODE_REL,
            type='d',
            offset='-2',
        ))
        self.assertEqual(self.period.date_from, '2016-12-30')
        self.assertEqual(self.period.date_to, '2016-12-30')
        self.assertTrue(self.period.valid)

    def test_rel_week(self):
        self.instance.write(dict(
            comparison_mode=True,
            date='2016-12-30'
        ))
        self.period.write(dict(
            mode=MODE_REL,
            type='w',
            offset='1',
            duration=2,
        ))
        # from Monday to Sunday, the week after 2016-12-30
        self.assertEqual(self.period.date_from, '2017-01-02')
        self.assertEqual(self.period.date_to, '2017-01-15')
        self.assertTrue(self.period.valid)

    def test_rel_date_range(self):
        # create a few date ranges
        date_range_type = self.env['date.range.type'].create(dict(
            name="Year",
        ))
        for year in (2016, 2017, 2018):
            self.env['date.range'].create(dict(
                type_id=date_range_type.id,
                name='%d' % year,
                date_start='%d-01-01' % year,
                date_end='%d-12-31' % year,
                company_id=False,
            ))
        self.instance.write(dict(
            comparison_mode=True,
            date='2017-06-15'
        ))
        self.period.write(dict(
            mode=MODE_REL,
            type='date_range',
            date_range_type_id=date_range_type.id,
            offset='-1',
            duration=3,
        ))
        self.assertEqual(self.period.date_from, '2016-01-01')
        self.assertEqual(self.period.date_to, '2018-12-31')
        self.assertTrue(self.period.valid)
