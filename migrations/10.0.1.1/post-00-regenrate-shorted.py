# -*- coding: utf-8 -*-

import logging
from odoo import api
logger = logging.getLogger('MIG compacted')


def migrate(cr, v):
    with api.Environment.manage():

        cr.execute("""UPDATE account_account SET compacted = FALSE WHERE compacted IS NULL;""")
