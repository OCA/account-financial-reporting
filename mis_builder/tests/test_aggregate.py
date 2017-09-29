# -*- coding: utf-8 -*-
# Copyright 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import doctest

from ..models import aggregate


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(aggregate))
    return tests
