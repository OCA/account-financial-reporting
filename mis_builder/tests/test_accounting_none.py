# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import doctest

from odoo.addons.mis_builder.models import accounting_none


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(accounting_none))
    return tests
