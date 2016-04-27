# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import re
from collections import defaultdict

from openerp.models import expression
from openerp.tools.safe_eval import safe_eval
from .accounting_none import AccountingNone

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

    def __init__(self, env):
        self.env = env
        # before done_parsing: {(domain, mode): set(account_codes)}
        # after done_parsing: {(domain, mode): list(account_ids)}
        self._map_account_ids = defaultdict(set)
        # {account_code: account_id} where account_code can be
        # - None for all accounts
        # - NNN% for a like
        # - NNN for a code with an exact match
        self._account_ids_by_code = defaultdict(set)

    def _load_account_codes(self, account_codes):
        account_model = self.env['account.account']
        exact_codes = set()
        for account_code in account_codes:
            if account_code in self._account_ids_by_code:
                continue
            if account_code is None:
                # None means we want all accounts
                account_ids = account_model.\
                    search([]).mapped('id')
                self._account_ids_by_code[account_code].update(account_ids)
            elif '%' in account_code:
                account_ids = account_model.\
                    search([('code', 'like', account_code)]).mapped('id')
                self._account_ids_by_code[account_code].update(account_ids)
            else:
                # search exact codes after the loop to do less queries
                exact_codes.add(account_code)
        for account in account_model.\
                search([('code', 'in', list(exact_codes))]):
            self._account_ids_by_code[account.code].add(account.id)

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
            account_codes = [None]  # None means we want all accounts
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

    def done_parsing(self):
        """Load account codes and replace account codes by
        account ids in map."""
        for key, account_codes in self._map_account_ids.items():
            # TODO _load_account_codes could be done
            # for all account_codes at once (also in v8)
            self._load_account_codes(account_codes)
            account_ids = set()
            for account_code in account_codes:
                account_ids.update(self._account_ids_by_code[account_code])
            self._map_account_ids[key] = list(account_ids)

    @classmethod
    def has_account_var(cls, expr):
        """Test if an string contains an accounting variable."""
        return bool(cls.ACC_RE.search(expr))

    def get_aml_domain_for_expr(self, expr,
                                date_from, date_to,
                                target_move):
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
                    self.get_aml_domain_for_dates(date_from, date_to,
                                                  mode, target_move)
        return expression.OR(aml_domains) + \
            expression.OR(date_domain_by_mode.values())

    def get_aml_domain_for_dates(self, date_from, date_to,
                                 mode,
                                 target_move):
        if mode == MODE_VARIATION:
            domain = [('date', '>=', date_from), ('date', '<=', date_to)]
        else:
            # for income and expense account, get balance from the beginning
            # of the current fiscal year
            fy_date_from = \
                self.company.compute_fiscalyear_dates(date_from)['date_from']
            domain = ['|',
                      ('date', '>=', fy_date_from),
                      ('account_id.user_type_id.include_initial_balance', '=',
                       True)]
            if mode == MODE_INITIAL:
                domain.append(('date', '<', date_from))
            elif mode == MODE_END:
                domain.append(('date', '<=', date_to))
        if target_move == 'posted':
            domain.append(('move_id.state', '=', 'posted'))
        return expression.normalize_domain(domain)

    def do_queries(self, date_from, date_to,
                   target_move, additional_move_line_filter=None):
        """Query sums of debit and credit for all accounts and domains
        used in expressions.

        This method must be executed after done_parsing().
        """
        aml_model = self.env['account.move.line']
        # {(domain, mode): {account_id: (debit, credit)}}
        self._data = defaultdict(dict)
        domain_by_mode = {}
        for key in self._map_account_ids:
            domain, mode = key
            if mode not in domain_by_mode:
                domain_by_mode[mode] = \
                    self.get_aml_domain_for_dates(date_from, date_to,
                                                  mode, target_move)
            domain = list(domain) + domain_by_mode[mode]
            domain.append(('account_id', 'in', self._map_account_ids[key]))
            if additional_move_line_filter:
                domain.extend(additional_move_line_filter)
            # fetch sum of debit/credit, grouped by account_id
            accs = aml_model.read_group(domain,
                                        ['debit', 'credit', 'account_id'],
                                        ['account_id'])
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
            v = AccountingNone
            for account_code in account_codes:
                account_ids = self._account_ids_by_code[account_code]
                for account_id in account_ids:
                    debit, credit = \
                        account_ids_data.get(account_id,
                                             (AccountingNone, AccountingNone))
                    if field == 'bal':
                        v += debit - credit
                    elif field == 'deb':
                        v += debit
                    elif field == 'crd':
                        v += credit
            return '(' + repr(v) + ')'
        return self.ACC_RE.sub(f, expr)
