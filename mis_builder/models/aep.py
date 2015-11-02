# -*- encoding: utf-8 -*-
##############################################################################
#
#    mis_builder module for Odoo, Management Information System Builder
#    Copyright (C) 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
#
#    This file is a part of mis_builder
#
#    mis_builder is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    mis_builder is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import re
from collections import defaultdict

from openerp.exceptions import Warning
from openerp import pooler
from openerp.osv import expression
from openerp.tools.safe_eval import safe_eval
from openerp.tools.translate import _

MODE_VARIATION = 'p'
MODE_INITIAL = 'i'
MODE_END = 'e'


class AccountingExpressionProcessor(object):
    """ Processor for accounting expressions.

    Expressions of the form <field><mode>[accounts][optional move line domain]
    are supported, where:
        * field is bal, crd, deb
        * mode is i (initial balance), e (ending balance),
          p (moves over period)
        * accounts is a list of accounts, possibly containing % wildcards
        * an optional domain on move lines allowing filters on eg analytic
          accounts or journal

    Examples:
        * bal[70]: variation of the balance of moves on account 70
          over the period (it is the same as balp[70]);
        * bali[70,60]: balance of accounts 70 and 60 at the start of period;
        * bale[1%]: balance of accounts starting with 1 at end of period.

    How to use:
        * repeatedly invoke parse_expr() for each expression containing
          accounting variables as described above; this lets the processor
          group domains and modes and accounts;
        * when all expressions have been parsed, invoke done_parsing()
          to notify the processor that it can prepare to query (mainly
          search all accounts - children, consolidation - that will need to
          be queried;
        * for each period, call do_queries(), then call replace_expr() for each
          expression to replace accounting variables with their resulting value
          for the given period.

    How it works:
        * by accumulating the expressions before hand, it ensures to do the
          strict minimum number of queries to the database (for each period,
          one query per domain and mode);
        * it queries using the orm read_group which reduces to a query with
          sum on debit and credit and group by on account_id (note: it seems
          the orm then does one query per account to fetch the account
          name...);
        * additionally, one query per view/consolidation account is done to
          discover the children accounts.
    """

    ACC_RE = re.compile(r"(?P<field>\bbal|\bcrd|\bdeb)"
                        r"(?P<mode>[pise])?"
                        r"(?P<accounts>_[a-zA-Z0-9]+|\[.*?\])"
                        r"(?P<domain>\[.*?\])?")

    def __init__(self, cursor):
        self.pool = pooler.get_pool(cursor.dbname)
        # before done_parsing: {(domain, mode): set(account_codes)}
        # after done_parsing: {(domain, mode): list(account_ids)}
        self._map_account_ids = defaultdict(set)
        self._account_ids_by_code = defaultdict(set)

    def _load_account_codes(self, cr, uid, account_codes, root_account,
                            context=None):
        account_obj = self.pool['account.account']
        exact_codes = set()
        like_codes = set()
        for account_code in account_codes:
            if account_code in self._account_ids_by_code:
                continue
            if account_code is None:
                # by convention the root account is keyed as
                # None in _account_ids_by_code, so it is consistent
                # with what _parse_match_object returns for an
                # empty list of account codes, ie [None]
                exact_codes.add(root_account.code)
            elif '%' in account_code:
                like_codes.add(account_code)
            else:
                exact_codes.add(account_code)
        account_ids = account_obj.search(
            cr, uid,
            [('code', 'in', list(exact_codes)),
             ('parent_id', 'child_of', root_account.id)],
            context=context)
        for account in account_obj.browse(
                cr, uid, account_ids, context=context):
            if account.code == root_account.code:
                code = None
            else:
                code = account.code
            if account.type in ('view', 'consolidation'):
                self._account_ids_by_code[code].update(
                    account_obj._get_children_and_consol(
                        cr, uid,
                        [account.id],
                        context=context))
            else:
                self._account_ids_by_code[code].add(account.id)
        for like_code in like_codes:
            for account_id in account_obj.\
                    search(cr, uid,
                           [('code', 'like', like_code),
                            ('parent_id', 'child_of', root_account.id)],
                           context=context):
                account = account_obj.browse(cr, uid, account_id,
                                             context=context)
                if account.type in ('view', 'consolidation'):
                    self._account_ids_by_code[like_code].update(
                        account_obj._get_children_and_consol(
                            cr, uid,
                            self.env.cr, self.env.uid,
                            [account.id],
                            context=context))
                else:
                    self._account_ids_by_code[like_code].add(account.id)

    def _parse_match_object(self, mo):
        """Split a match object corresponding to an accounting variable

        Returns field, mode, [account codes], (domain expression).
        """
        field, mode, account_codes, domain = mo.groups()
        if not mode:
            mode = MODE_VARIATION
        elif mode == 's':
            mode = MODE_END
        if account_codes.startswith('_'):
            account_codes = account_codes[1:]
        else:
            account_codes = account_codes[1:-1]
        if account_codes.strip():
            account_codes = [a.strip() for a in account_codes.split(',')]
        else:
            account_codes = [None]
        domain = domain or '[]'
        domain = tuple(safe_eval(domain))
        return field, mode, account_codes, domain

    def parse_expr(self, expr):
        """Parse an expression, extracting accounting variables.

        Domains and accounts are extracted and stored in the map
        so when all expressions have been parsed, we know which
        account codes to query for each domain and mode.
        """
        for mo in self.ACC_RE.finditer(expr):
            _, mode, account_codes, domain = self._parse_match_object(mo)
            key = (domain, mode)
            self._map_account_ids[key].update(account_codes)

    def done_parsing(self, cr, uid, root_account, context=None):
        """Load account codes and replace account codes by
        account ids in map."""
        for key, account_codes in self._map_account_ids.items():
            self._load_account_codes(cr, uid, account_codes, root_account,
                                     context=context)
            account_ids = set()
            for account_code in account_codes:
                account_ids.update(self._account_ids_by_code[account_code])
            self._map_account_ids[key] = list(account_ids)

    @classmethod
    def has_account_var(cls, expr):
        """Test if an string contains an accounting variable."""
        return bool(cls.ACC_RE.search(expr))

    def get_aml_domain_for_expr(self, cr, uid, expr,
                                date_from, date_to,
                                period_from, period_to,
                                target_move, context=None):
        """ Get a domain on account.move.line for an expression.

        Prerequisite: done_parsing() must have been invoked.

        Returns a domain that can be used to search on account.move.line.
        """
        aml_domains = []
        date_domain_by_mode = {}
        for mo in self.ACC_RE.finditer(expr):
            field, mode, account_codes, domain = self._parse_match_object(mo)
            aml_domain = list(domain)
            account_ids = set()
            for account_code in account_codes:
                account_ids.update(self._account_ids_by_code[account_code])
            aml_domain.append(('account_id', 'in', tuple(account_ids)))
            if field == 'crd':
                aml_domain.append(('credit', '>', 0))
            elif field == 'deb':
                aml_domain.append(('debit', '>', 0))
            aml_domains.append(expression.normalize_domain(aml_domain))
            if mode not in date_domain_by_mode:
                date_domain_by_mode[mode] = \
                    self.get_aml_domain_for_dates(cr, uid,
                                                  date_from, date_to,
                                                  period_from, period_to,
                                                  mode, target_move,
                                                  context=context)
        return expression.OR(aml_domains) + \
            expression.OR(date_domain_by_mode.values())

    def _period_has_moves(self, cr, uid, period, context=None):
        move_model = self.pool['account.move']
        return bool(move_model.search(cr, uid,
                                      [('period_id', '=', period.id)],
                                      limit=1, context=context))

    def _get_previous_opening_period(self, cr, uid, period, company_id,
                                     context=None):
        period_model = self.pool['account.period']
        period_ids = period_model.search(
            cr, uid,
            [('date_start', '<=', period.date_start),
             ('special', '=', True),
             ('company_id', '=', company_id)],
            order="date_start desc",
            limit=1,
            context=context)
        periods = period_model.browse(cr, uid, period_ids, context=context)
        return periods and periods[0]

    def _get_previous_normal_period(self, cr, uid, period, company_id,
                                    context=None):
        period_model = self.pool['account.period']
        period_ids = period_model.search(
            cr, uid,
            [('date_start', '<', period.date_start),
             ('special', '=', False),
             ('company_id', '=', company_id)],
            order="date_start desc",
            limit=1,
            context=context)
        periods = period_model.browse(cr, uid, period_ids, context=context)
        return periods and periods[0]

    def _get_first_normal_period(self, cr, uid, company_id, context=None):
        period_model = self.pool['account.period']
        period_ids = period_model.search(
            cr, uid,
            [('special', '=', False),
             ('company_id', '=', company_id)],
            order="date_start asc",
            limit=1,
            context=context)
        periods = period_model.browse(cr, uid, period_ids, context=context)
        return periods and periods[0]

    def _get_period_ids_between(self, cr, uid, period_from, period_to,
                                company_id, context=None):
        period_model = self.pool['account.period']
        period_ids = period_model.search(
            cr, uid,
            [('date_start', '>=', period_from.date_start),
             ('date_stop', '<=', period_to.date_stop),
             ('special', '=', False),
             ('company_id', '=', company_id)],
            context=context)
        if period_from.special:
            period_ids.append(period_from.id)
        return period_ids

    def _get_period_company_ids(self, cr, uid, period_from, period_to,
                                context=None):
        period_model = self.pool['account.period']
        period_ids = period_model.search(
            cr, uid,
            [('date_start', '>=', period_from.date_start),
             ('date_stop', '<=', period_to.date_stop),
             ('special', '=', False)],
            context=context)
        periods = period_model.browse(cr, uid, period_ids, context=context)
        return set([p.company_id.id for p in periods])

    def _get_period_ids_for_mode(self, cr, uid, period_from, period_to, mode,
                                 context=None):
        assert not period_from.special
        assert not period_to.special
        assert period_from.company_id == period_to.company_id
        assert period_from.date_start <= period_to.date_start
        period_ids = []
        for company_id in self._get_period_company_ids(cr, uid,
                                                       period_from, period_to,
                                                       context=context):
            if mode == MODE_VARIATION:
                period_ids.extend(self._get_period_ids_between(
                    cr, uid,
                    period_from, period_to, company_id,
                    context=context))
            else:
                if mode == MODE_INITIAL:
                    period_to = self._get_previous_normal_period(
                        cr, uid,
                        period_from, company_id,
                        context=context)
                # look for opening period with moves
                opening_period = self._get_previous_opening_period(
                    cr, uid,
                    period_from, company_id,
                    context=context)
                if opening_period and \
                        self._period_has_moves(cr, uid, opening_period,
                                               context=context):
                    # found opening period with moves
                    if opening_period.date_start == period_from.date_start and\
                            mode == MODE_INITIAL:
                        # if the opening period has the same start date as
                        # period_from, then we'll find the initial balance
                        # in the initial period and that's it
                        period_ids.append(opening_period.id)
                        continue
                    period_from = opening_period
                else:
                    # no opening period with moves,
                    # use very first normal period
                    period_from = self._get_first_normal_period(
                        cr, uid, company_id, context=context)
                if period_to:
                    period_ids.extend(self._get_period_ids_between(
                        cr, uid,
                        period_from, period_to, company_id,
                        context=context))
        return period_ids

    def get_aml_domain_for_dates(self, cr, uid, date_from, date_to,
                                 period_from, period_to,
                                 mode,
                                 target_move,
                                 context=None):
        if period_from and period_to:
            period_ids = self._get_period_ids_for_mode(
                cr, uid,
                period_from, period_to, mode,
                context=context)
            domain = [('period_id', 'in', period_ids)]
        else:
            if mode == MODE_VARIATION:
                domain = [('date', '>=', date_from), ('date', '<=', date_to)]
            else:
                raise Warning(_("Modes i and e are only applicable for "
                                "fiscal periods"))
        if target_move == 'posted':
            domain.append(('move_id.state', '=', 'posted'))
        return expression.normalize_domain(domain)

    def do_queries(self, cr, uid, date_from, date_to, period_from, period_to,
                   target_move, additional_move_line_filter=None,
                   context=None):
        """Query sums of debit and credit for all accounts and domains
        used in expressions.

        This method must be executed after done_parsing().
        """
        aml_model = self.pool['account.move.line']
        # {(domain, mode): {account_id: (debit, credit)}}
        self._data = defaultdict(dict)
        domain_by_mode = {}
        for key in self._map_account_ids:
            domain, mode = key
            if mode not in domain_by_mode:
                domain_by_mode[mode] = \
                    self.get_aml_domain_for_dates(cr, uid,
                                                  date_from, date_to,
                                                  period_from, period_to,
                                                  mode, target_move,
                                                  context=context)
            domain = list(domain) + domain_by_mode[mode]
            domain.append(('account_id', 'in', self._map_account_ids[key]))
            if additional_move_line_filter:
                domain.extend(additional_move_line_filter)
            # fetch sum of debit/credit, grouped by account_id
            accs = aml_model.read_group(cr, uid, domain,
                                        ['debit', 'credit', 'account_id'],
                                        ['account_id'],
                                        context=context)
            for acc in accs:
                self._data[key][acc['account_id'][0]] = \
                    (acc['debit'] or 0.0, acc['credit'] or 0.0)

    def replace_expr(self, expr):
        """Replace accounting variables in an expression by their amount.

        Returns a new expression string.

        This method must be executed after do_queries().
        """
        def f(mo):
            field, mode, account_codes, domain = self._parse_match_object(mo)
            key = (domain, mode)
            account_ids_data = self._data[key]
            v = 0.0
            for account_code in account_codes:
                account_ids = self._account_ids_by_code[account_code]
                for account_id in account_ids:
                    debit, credit = \
                        account_ids_data.get(account_id, (0.0, 0.0))
                    if field == 'bal':
                        v += debit - credit
                    elif field == 'deb':
                        v += debit
                    elif field == 'crd':
                        v += credit
            return '(' + repr(v) + ')'
        return self.ACC_RE.sub(f, expr)
