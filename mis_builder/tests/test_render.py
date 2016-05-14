# -*- coding: utf-8 -*-
# © 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import openerp.tests.common as common

from ..models.accounting_none import AccountingNone


class TestRendering(common.TransactionCase):

    def setUp(self):
        super(TestRendering, self).setUp()
        self.kpi = self.env['mis.report.kpi'].create(dict(
            name='testkpi',
            description='Test KPI',
            type='num',
            dp=0,
        ))
        self.lang = self.env['res.lang'].search([('code', '=', 'en_US')])[0]

    def test_render(self):
        self.assertEquals(u'1', self.kpi.render(self.lang, 1))
        self.assertEquals(u'1', self.kpi.render(self.lang, 1.1))
        self.assertEquals(u'2', self.kpi.render(self.lang, 1.6))
        self.kpi.dp = 2
        self.assertEquals(u'1.00', self.kpi.render(self.lang, 1))
        self.assertEquals(u'1.10', self.kpi.render(self.lang, 1.1))
        self.assertEquals(u'1.60', self.kpi.render(self.lang, 1.6))
        self.assertEquals(u'1.61', self.kpi.render(self.lang, 1.606))
        self.assertEquals(u'12,345.67', self.kpi.render(self.lang, 12345.67))

    def test_render_negative(self):
        # non breaking hyphen
        self.assertEquals(u'\u20111', self.kpi.render(self.lang, -1))

    def test_render_zero(self):
        self.assertEquals(u'0', self.kpi.render(self.lang, 0))
        self.assertEquals(u'', self.kpi.render(self.lang, None))
        self.assertEquals(u'', self.kpi.render(self.lang, AccountingNone))

    def test_render_suffix(self):
        self.kpi.suffix = u'€'
        self.assertEquals(u'1\xa0€', self.kpi.render(self.lang, 1))
        self.kpi.suffix = u'k€'
        self.kpi.divider = '1e3'
        self.assertEquals(u'1\xa0k€', self.kpi.render(self.lang, 1000))

    def test_render_prefix(self):
        self.kpi.prefix = u'$'
        self.assertEquals(u'$\xa01', self.kpi.render(self.lang, 1))
        self.kpi.prefix = u'k$'
        self.kpi.divider = '1e3'
        self.assertEquals(u'k$\xa01', self.kpi.render(self.lang, 1000))

    def test_render_divider(self):
        self.kpi.divider = '1e3'
        self.kpi.dp = 0
        self.assertEquals(u'1', self.kpi.render(self.lang, 1000))
        self.kpi.divider = '1e6'
        self.kpi.dp = 3
        self.assertEquals(u'0.001', self.kpi.render(self.lang, 1000))
        self.kpi.divider = '1e-3'
        self.kpi.dp = 0
        self.assertEquals(u'1,000', self.kpi.render(self.lang, 1))
        self.kpi.divider = '1e-6'
        self.kpi.dp = 0
        self.assertEquals(u'1,000,000', self.kpi.render(self.lang, 1))

    def test_render_pct(self):
        self.kpi.type = 'pct'
        self.assertEquals(u'100\xa0%', self.kpi.render(self.lang, 1))
        self.assertEquals(u'50\xa0%', self.kpi.render(self.lang, 0.5))
        self.kpi.dp = 2
        self.assertEquals(u'51.23\xa0%', self.kpi.render(self.lang, 0.5123))

    def test_render_string(self):
        self.kpi.type = 'str'
        self.assertEquals(u'', self.kpi.render(self.lang, ''))
        self.assertEquals(u'', self.kpi.render(self.lang, None))
        self.assertEquals(u'abcdé', self.kpi.render(self.lang, u'abcdé'))

    def test_compare_num_pct(self):
        self.assertEquals('pct', self.kpi.compare_method)
        self.assertEquals((1.0, u'+100.0\xa0%'),
                          self.kpi.compare_and_render(self.lang, 100, 50))
        self.assertEquals((0.5, u'+50.0\xa0%'),
                          self.kpi.compare_and_render(self.lang, 75, 50))
        self.assertEquals((0.5, u'+50.0\xa0%'),
                          self.kpi.compare_and_render(self.lang, -25, -50))
        self.assertEquals((1.0, u'+100.0\xa0%'),
                          self.kpi.compare_and_render(self.lang, 0, -50))
        self.assertEquals((2.0, u'+200.0\xa0%'),
                          self.kpi.compare_and_render(self.lang, 50, -50))
        self.assertEquals((-0.5, u'\u201150.0\xa0%'),
                          self.kpi.compare_and_render(self.lang, 25, 50))
        self.assertEquals((-1.0, u'\u2011100.0\xa0%'),
                          self.kpi.compare_and_render(self.lang, 0, 50))
        self.assertEquals((-2.0, u'\u2011200.0\xa0%'),
                          self.kpi.compare_and_render(self.lang, -50, 50))
        self.assertEquals((-0.5, u'\u201150.0\xa0%'),
                          self.kpi.compare_and_render(self.lang, -75, -50))
        self.assertEquals((AccountingNone, u''),
                          self.kpi.compare_and_render(
                              self.lang, 50, AccountingNone))
        self.assertEquals((AccountingNone, u''),
                          self.kpi.compare_and_render(
                              self.lang, 50, None))
        self.assertEquals((-1.0, u'\u2011100.0\xa0%'),
                          self.kpi.compare_and_render(
                              self.lang, AccountingNone, 50))
        self.assertEquals((-1.0, u'\u2011100.0\xa0%'),
                          self.kpi.compare_and_render(
                              self.lang, None, 50))

    def test_compare_num_diff(self):
        self.kpi.compare_method = 'diff'
        self.assertEquals((25, u'+25'),
                          self.kpi.compare_and_render(self.lang, 75, 50))
        self.assertEquals((-25, u'\u201125'),
                          self.kpi.compare_and_render(self.lang, 25, 50))
        self.kpi.suffix = u'€'
        self.assertEquals((-25, u'\u201125\xa0€'),
                          self.kpi.compare_and_render(self.lang, 25, 50))
        self.kpi.suffix = u''
        self.assertEquals((50.0, u'+50'),
                          self.kpi.compare_and_render(
                              self.lang, 50, AccountingNone))
        self.assertEquals((50.0, u'+50'),
                          self.kpi.compare_and_render(
                              self.lang, 50, None))
        self.assertEquals((-50.0, u'\u201150'),
                          self.kpi.compare_and_render(
                              self.lang, AccountingNone, 50))
        self.assertEquals((-50.0, u'\u201150'),
                          self.kpi.compare_and_render(
                              self.lang, None, 50))

    def test_compare_pct(self):
        self.kpi.type = 'pct'
        self.assertEquals((0.25, u'+25\xa0pp'),
                          self.kpi.compare_and_render(self.lang, 0.75, 0.50))
