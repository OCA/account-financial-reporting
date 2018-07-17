# -*- coding: utf-8 -*-
# © 2015 Yannick Vaucher (Camptocamp)
# © 2016 Damien Crier (Camptocamp)
# © 2016 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).-

import logging
_logger = logging.getLogger(__name__)

from . import abstract_report
from . import aged_partner_balance
from . import general_ledger
from . import open_items
from . import trial_balance

try:
    from . import abstract_report_xlsx
    from . import aged_partner_balance_xlsx
    from . import general_ledger_xlsx
    from . import open_items_xlsx
    from . import trial_balance_xlsx
except ImportError:
    _logger.info("ImportError raised while loading module.")
    _logger.debug("ImportError details:", exc_info=True)
