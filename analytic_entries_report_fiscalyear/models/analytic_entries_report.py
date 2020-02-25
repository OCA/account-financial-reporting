# -*- coding: utf-8 -*-
# © 2015 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import collections
try:
    import sqlparse
except ImportError as err:
    import logging
    logging.debug(err)
import datetime
from psycopg2.extensions import AsIs
from dateutil.relativedelta import relativedelta
from openerp import api, models, fields


class AnalyticEntriesReport(models.Model):
    _inherit = 'analytic.entries.report'

    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Fiscal year')
    period_id = fields.Many2one('account.period', 'Fiscal period')

    def init(self, cr):
        """Here, we try to be less invasive than the usual blunt overwrite of
        the sql view"""
        # added joins to account_period & account_move_line
        # added appropriate fields to select list and group by
        super(AnalyticEntriesReport, self).init(cr)
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
                        sqlparse.tokens.Generic,
                        ',coalesce(ml.period_id, p.id) as period_id,'
                        'coalesce(p_from_move.fiscalyear_id, p.fiscalyear_id) '
                        'as fiscalyear_id'
                    ))
                if isinstance(
                    token,
                    (sqlparse.sql.IdentifierList, sqlparse.sql.Parenthesis)
                ) and current_keyword.value == 'FROM':
                    def find_table(token):
                        if isinstance(token, sqlparse.sql.Identifier) and\
                           token.get_real_name() == 'account_analytic_line':
                            return token
                        if not isinstance(token, collections.Iterable):
                            return
                        for child_token in token:
                            result = find_table(child_token)
                            if result:
                                return result

                    table = find_table(token)
                    assert table

                    table.parent.insert_after(table, sqlparse.sql.Token(
                        sqlparse.tokens.Generic,
                        ' left outer join account_period p '
                        'on p.special = False and p.date_start <= a.date '
                        'and p.date_stop >= a.date '
                        'left outer join account_move_line ml '
                        'on a.move_id = ml.id '
                        'left outer join account_period p_from_move '
                        'on ml.period_id = p_from_move.id '))
                if isinstance(token, sqlparse.sql.IdentifierList) and\
                   current_keyword.value == 'GROUP BY':
                    last = None
                    for last in token:
                        pass
                    token.insert_after(last, sqlparse.sql.Token(
                        sqlparse.tokens.Generic,
                        ', coalesce(p_from_move.fiscalyear_id,'
                        'p.fiscalyear_id),'
                        'coalesce(ml.period_id, p.id)'))
        cr.execute("create or replace view %s as (%s)",
                   (AsIs(self._table), AsIs(str(statement)[:-1])))

    @api.model
    def _apply_custom_operators(self, domain):
        adjusted_domain = []

        for proposition in domain:
            if not isinstance(proposition, tuple) and\
                    not isinstance(proposition, list) or\
                    len(proposition) != 3:
                # we can't use expression.is_leaf here because of our custom
                # operator
                adjusted_domain.append(proposition)
                continue
            field, operator, value = proposition
            if field.endswith('fiscalyear_id') and operator == 'offset':
                date = datetime.date.today() + relativedelta(years=value)
                fiscalyear_id = self.env['account.fiscalyear'].find(dt=date)
                adjusted_domain.append((field, '=', fiscalyear_id))
            elif field.endswith('period_id') and operator == 'offset':
                current_period = self.env['account.period'].with_context(
                    account_period_prefer_normal=True).find()

                direction = '>='
                if value < 0:
                    direction = '<='

                periods = current_period.search(
                    [
                        ('date_start', direction, current_period.date_start),
                        ('special', '=', False),
                    ], limit=(abs(value) + 1) or 1, order='date_start ' +
                    ('asc' if direction == '>=' else 'desc')
                )

                adjusted_domain.append((field, '=', periods[value].id))
            else:
                adjusted_domain.append(proposition)

        return adjusted_domain

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        '''Override read_group to respect filters whose domain can't be
        computed on the client side'''
        adjusted_domain = self._apply_custom_operators(domain)
        return super(AnalyticEntriesReport, self).read_group(
            adjusted_domain, fields, groupby,
            offset=offset, limit=limit, orderby=orderby, lazy=lazy)
