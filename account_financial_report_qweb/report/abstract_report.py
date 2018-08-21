# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models


class AbstractReport(models.AbstractModel):
    _name = 'report_qweb_abstract'

    def _transient_clean_rows_older_than(self, cr, seconds):
        assert self._transient, \
            "Model %s is not transient, it cannot be vacuumed!" % self._name
        # Never delete rows used in last 5 minutes
        seconds = max(seconds, 300)
        query = """
DELETE FROM """ + self._table + """
WHERE
    COALESCE(write_date, create_date, (now() at time zone 'UTC'))::timestamp
    < ((now() at time zone 'UTC') - interval %s)
"""
        cr.execute(query, ("%s seconds" % seconds,))
