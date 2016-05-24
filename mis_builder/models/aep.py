# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import re
from collections import defaultdict
from itertools import izip

from openerp import fields
from openerp.models import expression
from openerp.tools.safe_eval import safe_eval
from openerp.tools.float_utils import float_is_zero
from .accounting_none import AccountingNone


class AccountingExpressionProcessor(object):
    """ Processor for accounting expressions.

    Expressions of the form <field><mode>[accounts][optional move line domain]
    are supported, where:
        * field is bal, crd, deb
        * mode is i (initial balance), e (ending balance),
          p (moves over period)
        * there is also a special u mode (unallocated P&L) which computes
          the sum from the beginning until the beginning of the fiscal year
          of the period; it is only meaningful for P&L accounts
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
    MODE_VARIATION = 'p'
    MODE_INITIAL = 'i'
    MODE_END = 'e'
    MODE_UNALLOCATED = 'u'

    _ACC_RE = re.compile(r"(?P<field>\bbal|\bcrd|\bdeb)"
                         r"(?P<mode>[piseu])?"
                         r"(?P<accounts>_[a-zA-Z0-9]+|\[.*?\])"
                         r"(?P<domain>\[.*?\])?")

    def __init__(self, company):
        self.company = company
        self.dp = company.currency_id.decimal_places
        # before done_parsing: {(domain, mode): set(account_codes)}
        # after done_parsing: {(domain, mode): list(account_ids)}
        self._map_account_ids = defaultdict(set)
        # {account_code: account_id} where account_code can be
        # - None for all accounts
        # - NNN% for a like
        # - NNN for a code with an exact match
        self._account_ids_by_code = defaultdict(set)
        # smart ending balance (returns AccountingNone if there
        # are no moves in period and 0 initial balance), implies
        # a first query to get the initial balance and another
        # to get the variation, so it's a bit slower
        self.smart_end = True

    def _load_account_codes(self, account_codes):
        account_model = self.company.env['account.account']
        exact_codes = set()
        for account_code in account_codes:
            if account_code in self._account_ids_by_code:
                continue
            if account_code is None:
                # None means we want all accounts
                account_ids = account_model.\
                    search([('company_id', '=', self.company.id)]).ids
                self._account_ids_by_code[account_code].update(account_ids)
            elif '%' in account_code:
                account_ids = account_model.\
                    search([('code', '=like', account_code),
                            ('company_id', '=', self.company.id)]).ids
                self._account_ids_by_code[account_code].update(account_ids)
            else:
                # search exact codes after the loop to do less queries
                exact_codes.add(account_code)
        for account in account_model.\
                search([('code', 'in', list(exact_codes)),
                        ('company_id', '=', self.company.id)]):
            self._account_ids_by_code[account.code].add(account.id)

    def _parse_match_object(self, mo):
        """Split a match object corresponding to an accounting variable

        Returns field, mode, [account codes], (domain expression).
        """
        field, mode, account_codes, domain = mo.groups()
        if not mode:
            mode = self.MODE_VARIATION
        elif mode == 's':
            mode = self.MODE_END
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
        for mo in self._ACC_RE.finditer(expr):
            _, mode, account_codes, domain = self._parse_match_object(mo)
            if mode == self.MODE_END and self.smart_end:
                modes = (self.MODE_INITIAL, self.MODE_VARIATION, self.MODE_END)
            else:
                modes = (mode, )
            for mode in modes:
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
        return bool(cls._ACC_RE.search(expr))

    def get_aml_domain_for_expr(self, expr,
                                date_from, date_to,
                                target_move,
                                account_id=None):
        """ Get a domain on account.move.line for an expression.

        Prerequisite: done_parsing() must have been invoked.

        Returns a domain that can be used to search on account.move.line.
        """
        aml_domains = []
        date_domain_by_mode = {}
        for mo in self._ACC_RE.finditer(expr):
            field, mode, account_codes, domain = self._parse_match_object(mo)
            aml_domain = list(domain)
            account_ids = set()
            for account_code in account_codes:
                account_ids.update(self._account_ids_by_code[account_code])
            if not account_id:
                aml_domain.append(('account_id', 'in', tuple(account_ids)))
            else:
                # filter on account_id
                if account_id in account_ids:
                    aml_domain.append(('account_id', '=', account_id))
                else:
                    continue
            if field == 'crd':
                aml_domain.append(('credit', '>', 0))
            elif field == 'deb':
                aml_domain.append(('debit', '>', 0))
            aml_domains.append(expression.normalize_domain(aml_domain))
            if mode not in date_domain_by_mode:
                date_domain_by_mode[mode] = \
                    self.get_aml_domain_for_dates(date_from, date_to,
                                                  mode, target_move)
        assert aml_domains
        return expression.OR(aml_domains) + \
            expression.OR(date_domain_by_mode.values())

    def get_aml_domain_for_dates(self, date_from, date_to,
                                 mode,
                                 target_move):
        if mode == self.MODE_VARIATION:
            domain = [('date', '>=', date_from), ('date', '<=', date_to)]
        elif mode in (self.MODE_INITIAL, self.MODE_END):
            # for income and expense account, sum from the beginning
            # of the current fiscal year only, for balance sheet accounts
            # sum from the beginning of time
            date_from_date = fields.Date.from_string(date_from)
            fy_date_from = \
                self.company.\
                compute_fiscalyear_dates(date_from_date)['date_from']
            domain = ['|',
                      ('date', '>=', fields.Date.to_string(fy_date_from)),
                      ('user_type_id.include_initial_balance', '=', True)]
            if mode == self.MODE_INITIAL:
                domain.append(('date', '<', date_from))
            elif mode == self.MODE_END:
                domain.append(('date', '<=', date_to))
        elif mode == self.MODE_UNALLOCATED:
            date_from_date = fields.Date.from_string(date_from)
            fy_date_from = \
                self.company.\
                compute_fiscalyear_dates(date_from_date)['date_from']
            domain = [('date', '<', fields.Date.to_string(fy_date_from)),
                      ('user_type_id.include_initial_balance', '=', False)]
        if target_move == 'posted':
            domain.append(('move_id.state', '=', 'posted'))
        return expression.normalize_domain(domain)

    def do_queries(self, date_from, date_to,
                   target_move='posted', additional_move_line_filter=None):
        """Query sums of debit and credit for all accounts and domains
        used in expressions.

        This method must be executed after done_parsing().
        """
        aml_model = self.company.env['account.move.line']
        # {(domain, mode): {account_id: (debit, credit)}}
        self._data = defaultdict(dict)
        domain_by_mode = {}
        ends = []
        for key in self._map_account_ids:
            domain, mode = key
            if mode == self.MODE_END and self.smart_end:
                # postpone computation of ending balance
                ends.append((domain, mode))
                continue
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
                debit = acc['debit'] or 0.0
                credit = acc['credit'] or 0.0
                if mode in (self.MODE_INITIAL, self.MODE_UNALLOCATED) and \
                        float_is_zero(debit-credit,
                                      precision_rounding=self.dp):
                    # in initial mode, ignore accounts with 0 balance
                    continue
                self._data[key][acc['account_id'][0]] = (debit, credit)
        # compute ending balances by summing initial and variation
        for key in ends:
            domain, mode = key
            initial_data = self._data[(domain, self.MODE_INITIAL)]
            variation_data = self._data[(domain, self.MODE_VARIATION)]
            account_ids = set(initial_data.keys()) | set(variation_data.keys())
            for account_id in account_ids:
                di, ci = initial_data.get(account_id,
                                          (AccountingNone, AccountingNone))
                dv, cv = variation_data.get(account_id,
                                            (AccountingNone, AccountingNone))
                self._data[key][account_id] = (di + dv, ci + cv)

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
            # in initial balance mode, assume 0 is None
            # as it does not make sense to distinguish 0 from "no data"
            if v is not AccountingNone and \
                    mode in (self.MODE_INITIAL, self.MODE_UNALLOCATED) and \
                    float_is_zero(v, precision_rounding=self.dp):
                v = AccountingNone
            return '(' + repr(v) + ')'

        return self._ACC_RE.sub(f, expr)

    def replace_exprs_by_account_id(self, exprs):
        """Replace accounting variables in a list of expression
        by their amount, iterating by accounts involved in the expression.

        yields account_id, replaced_expr

        This method must be executed after do_queries().
        """
        def f(mo):
            field, mode, account_codes, domain = self._parse_match_object(mo)
            key = (domain, mode)
            account_ids_data = self._data[key]
            debit, credit = \
                account_ids_data.get(account_id,
                                     (AccountingNone, AccountingNone))
            if field == 'bal':
                v = debit - credit
            elif field == 'deb':
                v = debit
            elif field == 'crd':
                v = credit
            # in initial balance mode, assume 0 is None
            # as it does not make sense to distinguish 0 from "no data"
            if v is not AccountingNone and \
                    mode in (self.MODE_INITIAL, self.MODE_UNALLOCATED) and \
                    float_is_zero(v, precision_rounding=self.dp):
                v = AccountingNone
            return '(' + repr(v) + ')'

        account_ids = set()
        for expr in exprs:
            for mo in self._ACC_RE.finditer(expr):
                field, mode, account_codes, domain = \
                    self._parse_match_object(mo)
                key = (domain, mode)
                account_ids_data = self._data[key]
                for account_code in account_codes:
                    for account_id in self._account_ids_by_code[account_code]:
                        if account_id in account_ids_data:
                            account_ids.add(account_id)

        for account_id in account_ids:
            yield account_id, [self._ACC_RE.sub(f, expr) for expr in exprs]

    @classmethod
    def _get_balances(cls, mode, company, date_from, date_to,
                      target_move='posted'):
        expr = 'deb{mode}[], crd{mode}[]'.format(mode=mode)
        aep = AccountingExpressionProcessor(company)
        # disable smart_end to have the data at once, instead
        # of initial + variation
        aep.smart_end = False
        aep.parse_expr(expr)
        aep.done_parsing()
        aep.do_queries(date_from, date_to, target_move)
        return aep._data[((), mode)]

    @classmethod
    def get_balances_initial(cls, company, date, target_move='posted'):
        """ A convenience method to obtain the initial balances of all accounts
        at a given date.

        It is the same as get_balances_end(date-1).

        :param company:
        :param date:
        :param target_move: if 'posted', consider only posted moves

        Returns a dictionary: {account_id, (debit, credit)}
        """
        return cls._get_balances(cls.MODE_INITIAL, company,
                                 date, date, target_move)

    @classmethod
    def get_balances_end(cls, company, date, target_move='posted'):
        """ A convenience method to obtain the ending balances of all accounts
        at a given date.

        It is the same as get_balances_initial(date+1).

        :param company:
        :param date:
        :param target_move: if 'posted', consider only posted moves

        Returns a dictionary: {account_id, (debit, credit)}
        """
        return cls._get_balances(cls.MODE_END, company,
                                 date, date, target_move)

    @classmethod
    def get_balances_variation(cls, company, date_from, date_to,
                               target_move='posted'):
        """ A convenience method to obtain the variation of the
        balances of all accounts over a period.

        :param company:
        :param date:
        :param target_move: if 'posted', consider only posted moves

        Returns a dictionary: {account_id, (debit, credit)}
        """
        return cls._get_balances(cls.MODE_VARIATION, company,
                                 date_from, date_to, target_move)

    @classmethod
    def get_unallocated_pl(cls, company, date, target_move='posted'):
        """ A convenience method to obtain the unallocated profit/loss
        of the previous fiscal years at a given date.

        :param company:
        :param date:
        :param target_move: if 'posted', consider only posted moves

        Returns a tuple (debit, credit)
        """
        # TODO shoud we include here the accounts of type "unaffected"
        # or leave that to the caller?
        bals = cls._get_balances(cls.MODE_UNALLOCATED, company,
                                 date, date, target_move)
        return tuple(map(sum, izip(*bals.values())))
