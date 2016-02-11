# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

try:
    from . import mis_builder_xls
except ImportError:
    pass  # this module is not installed

from . import report_mis_report_instance
