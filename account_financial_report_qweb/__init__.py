# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import models
from . import wizard

# Don't break installations that don't have this module installed
have_report_xlsx = False
try:
    from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
    have_report_xlsx = True
except ImportError:
    import logging
    logging.getLogger(__name__).warn('Module report_xlsx is not available')

if have_report_xlsx:
    from . import report
