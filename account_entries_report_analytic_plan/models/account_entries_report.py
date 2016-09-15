# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import sqlparse
from psycopg2.extensions import AsIs
from openerp import fields, models


class AccountEntriesReport(models.Model):
    _inherit = 'account.entries.report'

    analytics_id = fields.Many2one('account.analytic.plan.instance',
                                   'Analytic Distribution')

    def init(self, cr):
        """Here, we try to be less invasive than the usual blunt overwrite of
        the sql view"""
        super(AccountEntriesReport, self).init(cr)
        cr.execute("select pg_get_viewdef(%s::regclass)", (self._table,))
        for statement in sqlparse.parse(cr.fetchone()[0]):
            current_keyword = None
            for token in statement:
                if token.is_keyword:
                    current_keyword = token
                if isinstance(token, sqlparse.sql.IdentifierList) and\
                   current_keyword.value == 'SELECT':
                    last = None
                    for last in token:
                        pass
                    token.insert_after(last, sqlparse.sql.Token(
                        sqlparse.tokens.Generic, ',l.analytics_id'))
        cr.execute("create or replace view %s as (%s)",
                   (AsIs(self._table), AsIs(str(statement)[:-1])))
