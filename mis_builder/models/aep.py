import re
from collections import defaultdict

from openerp.osv import expression
from openerp.tools.safe_eval import safe_eval


class AccountingExpressionProcessor(object):
    """ Processor for accounting expressions.

    Expressions of the form <field><mode>[accounts][optional move line domain]
    are supported, where:
        * field is bal, crd, deb
        * mode is i (initial balance), e (ending balance),
          p (moves over period)
        * accounts is a list of accounts, possibly containing % wildcards
        * an optional domain on analytic lines allowing filters on eg analytic
          accounts or journal

    Examples:
        * bal[70]: balance of moves on account 70 over the period
          (it is the same as balp[70]);
        * bali[70,60]: initial balance of accounts 70 and 60;
        * bale[1%]: balance of accounts starting with 1 at end of period.

    How to use:
        * repeatedly invoke parse_expr() for each expression containing
          accounting variables as described above; this let the processor
          group domains and modes and accounts;
        * when all expressions have been parsed, invoke done_parsing()
          to notify the processor that it can prepare to query (mainly
          search all accounts - children, consolidation - that will need to
          be queried;
        * for each period, call do_queries(), then call replace_expr() for each
          expression to replace accounting variables with their resulting value
          for the given period.

    How it works:
        * by accumulating the expressions before hand, it ensure to do the
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
                        r"(?P<accounts>_[0-9]+|\[.*?\])"
                        r"(?P<domain>\[.*?\])?")

    def __init__(self, env):
        self.env = env
        self._map = defaultdict(set)  # {(domain, mode): set(account_ids)}
        self._account_ids_by_code = defaultdict(set)

    def _load_account_codes(self, account_codes, account_domain):
        account_model = self.env['account.account']
        # TODO: account_obj is necessary because _get_children_and_consol
        #       does not work in new API?
        account_obj = self.env.registry('account.account')
        exact_codes = set()
        like_codes = set()
        for account_code in account_codes:
            if account_code in self._account_ids_by_code:
                continue
            if '%' in account_code:
                like_codes.add(account_code)
            else:
                exact_codes.add(account_code)
        for account in account_model.\
                search([('code', 'in', list(exact_codes))] + account_domain):
            if account.type in ('view', 'consolidation'):
                self._account_ids_by_code[account.code].update(
                    account_obj._get_children_and_consol(
                        self.env.cr, self.env.uid,
                        [account.id],
                        self.env.context))
            else:
                self._account_ids_by_code[account.code].add(account.id)
        for like_code in like_codes:
            for account in account_model.\
                    search([('code', 'like', like_code)] + account_domain):
                if account.type in ('view', 'consolidation'):
                    self._account_ids_by_code[like_code].update(
                        account_obj._get_children_and_consol(
                            self.env.cr, self.env.uid,
                            [account.id],
                            self.env.context))
                else:
                    self._account_ids_by_code[like_code].add(account.id)

    def _parse_mo(self, mo):
        """Split a match object corresponding to an accounting variable

        Returns field, mode, [account codes], [domain expression].
        """
        field, mode, account_codes, domain = mo.groups()
        if not mode:
            mode = 'p'
        elif mode == 's':
            mode = 'e'
        if account_codes.startswith('_'):
            account_codes = account_codes[1:]
        else:
            account_codes = account_codes[1:-1]
        account_codes = [a.strip() for a in account_codes.split(',')]
        domain = domain or '[]'
        domain = tuple(safe_eval(domain))
        return field, mode, account_codes, domain

    def parse_expr(self, expr):
        """Parse an expression, extracting accounting variables.

        Domains and accounts are extracted and stored in the map
        so when all expressions have been parsed, we know what to query.
        """
        for mo in self.ACC_RE.finditer(expr):
            field, mode, account_codes, domain = self._parse_mo(mo)
            key = (domain, mode)
            self._map[key].update(account_codes)

    def done_parsing(self, account_domain):
        # load account codes and replace account codes by account ids in _map
        for key, account_codes in self._map.items():
            self._load_account_codes(account_codes, account_domain)
            account_ids = set()
            for account_code in account_codes:
                account_ids.update(self._account_ids_by_code[account_code])
            self._map[key] = list(account_ids)

    def get_aml_domain_for_expr(self, expr):
        """ Get a domain on account.move.line for an expression.

        Only accounting expression in mode 'p' and 'e' are considered.

        Prerequisite: done_parsing() must have been invoked.

        Returns a domain that can be used to search on account.move.line.
        """
        domains = []
        for mo in self.ACC_RE.finditer(expr):
            field, mode, account_codes, domain_partial = self._parse_mo(mo)
            if mode == 'i':
                continue
            account_ids = set()
            for account_code in account_codes:
                account_ids.update(self._account_ids_by_code[account_code])
            domain = [('account_id', 'in', tuple(account_ids))]
            domain.extend(list(domain_partial))
            if field == 'crd':
                domain.append(('credit', '>', 0))
            elif field == 'deb':
                domain.append(('debit', '>', 0))
            domain.extend(domain)
            domains.append(expression.normalize_domain(domain))
        return expression.OR(domains)

    def do_queries(self, period_domain, period_domain_i, period_domain_e):
        aml_model = self.env['account.move.line']
        self._data = {}  # {(domain, mode): {account_id: (debit, credit)}}
        for key in self._map:
            self._data[key] = {}
            domain, mode = key
            if mode == 'p':
                domain = list(domain) + period_domain
            elif mode == 'i':
                domain = list(domain) + period_domain_i
            elif mode == 'e':
                domain = list(domain) + period_domain_e
            else:
                raise RuntimeError("unexpected mode %s" % (mode,))
            domain = [('account_id', 'in', self._map[key])] + domain
            accs = aml_model.read_group(domain,
                                        ['debit', 'credit', 'account_id'],
                                        ['account_id'])
            for acc in accs:
                self._data[key][acc['account_id'][0]] = \
                    (acc['debit'], acc['credit'])

    def replace_expr(self, expr):
        """Replace accounting variables in an expression by their amount.

        Returns a new expression.

        This method must be executed after do_queries().
        """
        def f(mo):
            field, mode, account_codes, domain = self._parse_mo(mo)
            key = (domain, mode)
            account_ids_data = self._data[key]
            v = 0.0
            for account_code in account_codes:
                for account_id in self._account_ids_by_code[account_code]:
                    debit, credit = \
                        account_ids_data.get(account_id, (0.0, 0.0))
                    if field == 'deb':
                        v += debit
                    elif field == 'crd':
                        v += credit
                    elif field == 'bal':
                        v += debit - credit
            return '(' + repr(v) + ')'
        return self.ACC_RE.sub(f, expr)
