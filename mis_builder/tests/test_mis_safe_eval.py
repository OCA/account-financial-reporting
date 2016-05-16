# -*- coding: utf-8 -*-
# © 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import openerp.tests.common as common

from ..models.mis_safe_eval import mis_safe_eval, DataError, NameDataError


class TestMisSafeEval(common.TransactionCase):

    def test_nominal(self):
        val = mis_safe_eval('a + 1', {'a': 1})
        self.assertEqual(val, 2)

    def test_exceptions(self):
        val = mis_safe_eval('1/0', {})  # division by zero
        self.assertTrue(isinstance(val, DataError))
        self.assertEqual(val.name, '#DIV/0')
        val = mis_safe_eval('1a', {})  # syntax error
        self.assertTrue(isinstance(val, DataError))
        self.assertEqual(val.name, '#ERR')

    def test_name_error(self):
        val = mis_safe_eval('a + 1', {})
        self.assertTrue(isinstance(val, NameDataError))
        self.assertEqual(val.name, '#NAME')
