# -*- coding: utf-8 -*-
# © 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import openerp.tests.common as common

from ..models.accounting_none import AccountingNone
from ..models.mis_report_style import (
    TYPE_NUM, TYPE_PCT, TYPE_STR, CMP_DIFF, CMP_PCT
)


class TestRendering(common.TransactionCase):

    def setUp(self):
        super(TestRendering, self).setUp()
        self.style_obj = self.env['mis.report.style']
        self.kpi_obj = self.env['mis.report.kpi']
        self.style = self.style_obj.create(dict(
            name='teststyle',
        ))
        self.lang = self.env['res.lang'].search([('code', '=', 'en_US')])[0]

    def _render(self, value, type=TYPE_NUM):
        style_props = self.style_obj.merge([self.style])
        return self.style_obj.render(self.lang, style_props, type, value)

    def _compare_and_render(self, value, base_value,
                            type=TYPE_NUM, compare_method=CMP_PCT):
        style_props = self.style_obj.merge([self.style])
        return self.style_obj.compare_and_render(self.lang, style_props,
                                                 type, compare_method,
                                                 value, base_value)[:2]

    def test_render(self):
        self.assertEquals(u'1', self._render(1))
        self.assertEquals(u'1', self._render(1.1))
        self.assertEquals(u'2', self._render(1.6))
        self.style.dp_inherit = False
        self.style.dp = 2
        self.assertEquals(u'1.00', self._render(1))
        self.assertEquals(u'1.10', self._render(1.1))
        self.assertEquals(u'1.60', self._render(1.6))
        self.assertEquals(u'1.61', self._render(1.606))
        self.assertEquals(u'12,345.67', self._render(12345.67))

    def test_render_negative(self):
        # non breaking hyphen
        self.assertEquals(u'\u20111', self._render(-1))

    def test_render_zero(self):
        self.assertEquals(u'0', self._render(0))
        self.assertEquals(u'', self._render(None))
        self.assertEquals(u'', self._render(AccountingNone))

    def test_render_suffix(self):
        self.style.suffix_inherit = False
        self.style.suffix = u'€'
        self.assertEquals(u'1\xa0€', self._render(1))
        self.style.suffix = u'k€'
        self.style.divider_inherit = False
        self.style.divider = '1e3'
        self.assertEquals(u'1\xa0k€', self._render(1000))

    def test_render_prefix(self):
        self.style.prefix_inherit = False
        self.style.prefix = u'$'
        self.assertEquals(u'$\xa01', self._render(1))
        self.style.prefix = u'k$'
        self.style.divider_inherit = False
        self.style.divider = '1e3'
        self.assertEquals(u'k$\xa01', self._render(1000))

    def test_render_divider(self):
        self.style.divider_inherit = False
        self.style.divider = '1e3'
        self.style.dp_inherit = False
        self.style.dp = 0
        self.assertEquals(u'1', self._render(1000))
        self.style.divider = '1e6'
        self.style.dp = 3
        self.assertEquals(u'0.001', self._render(1000))
        self.style.divider = '1e-3'
        self.style.dp = 0
        self.assertEquals(u'1,000', self._render(1))
        self.style.divider = '1e-6'
        self.style.dp = 0
        self.assertEquals(u'1,000,000', self._render(1))

    def test_render_pct(self):
        self.assertEquals(u'100\xa0%', self._render(1, TYPE_PCT))
        self.assertEquals(u'50\xa0%', self._render(0.5, TYPE_PCT))
        self.style.dp_inherit = False
        self.style.dp = 2
        self.assertEquals(u'51.23\xa0%', self._render(0.5123, TYPE_PCT))

    def test_render_string(self):
        self.assertEquals(u'', self._render('', TYPE_STR))
        self.assertEquals(u'', self._render(None, TYPE_STR))
        self.assertEquals(u'abcdé', self._render(u'abcdé', TYPE_STR))

    def test_compare_num_pct(self):
        self.assertEquals((1.0, u'+100.0\xa0%'),
                          self._compare_and_render(100, 50))
        self.assertEquals((0.5, u'+50.0\xa0%'),
                          self._compare_and_render(75, 50))
        self.assertEquals((0.5, u'+50.0\xa0%'),
                          self._compare_and_render(-25, -50))
        self.assertEquals((1.0, u'+100.0\xa0%'),
                          self._compare_and_render(0, -50))
        self.assertEquals((2.0, u'+200.0\xa0%'),
                          self._compare_and_render(50, -50))
        self.assertEquals((-0.5, u'\u201150.0\xa0%'),
                          self._compare_and_render(25, 50))
        self.assertEquals((-1.0, u'\u2011100.0\xa0%'),
                          self._compare_and_render(0, 50))
        self.assertEquals((-2.0, u'\u2011200.0\xa0%'),
                          self._compare_and_render(-50, 50))
        self.assertEquals((-0.5, u'\u201150.0\xa0%'),
                          self._compare_and_render(-75, -50))
        self.assertEquals((AccountingNone, u''),
                          self._compare_and_render(50, AccountingNone))
        self.assertEquals((AccountingNone, u''),
                          self._compare_and_render(50, None))
        self.assertEquals((-1.0, u'\u2011100.0\xa0%'),
                          self._compare_and_render(AccountingNone, 50))
        self.assertEquals((-1.0, u'\u2011100.0\xa0%'),
                          self._compare_and_render(None, 50))

    def test_compare_num_diff(self):
        self.assertEquals((25, u'+25'),
                          self._compare_and_render(75, 50,
                                                   TYPE_NUM, CMP_DIFF))
        self.assertEquals((-25, u'\u201125'),
                          self._compare_and_render(25, 50,
                                                   TYPE_NUM, CMP_DIFF))
        self.style.suffix_inherit = False
        self.style.suffix = u'€'
        self.assertEquals((-25, u'\u201125\xa0€'),
                          self._compare_and_render(25, 50,
                                                   TYPE_NUM, CMP_DIFF))
        self.style.suffix = u''
        self.assertEquals((50.0, u'+50'),
                          self._compare_and_render(50, AccountingNone,
                                                   TYPE_NUM, CMP_DIFF))
        self.assertEquals((50.0, u'+50'),
                          self._compare_and_render(50, None,
                                                   TYPE_NUM, CMP_DIFF))
        self.assertEquals((-50.0, u'\u201150'),
                          self._compare_and_render(AccountingNone, 50,
                                                   TYPE_NUM, CMP_DIFF))
        self.assertEquals((-50.0, u'\u201150'),
                          self._compare_and_render(None, 50,
                                                   TYPE_NUM, CMP_DIFF))

    def test_compare_pct(self):
        self.assertEquals((0.25, u'+25\xa0pp'),
                          self._compare_and_render(0.75, 0.50, TYPE_PCT))
