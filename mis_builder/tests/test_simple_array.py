# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import doctest

from openerp.addons.mis_builder.models import simple_array


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(simple_array))
    return tests
