# -*- coding: utf-8 -*-
try:
    from . import report
    from . import wizard
except ImportError:
    import logging
    logging.getLogger('openerp.module').warning('''report_xlsx not available in
    addons path. account_financial_report_webkit_xlsx will not be usable''')
