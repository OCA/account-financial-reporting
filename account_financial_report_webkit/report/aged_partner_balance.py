# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from __future__ import division
from datetime import datetime

from openerp.modules.registry import RegistryManager
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from .open_invoices import PartnersOpenInvoicesWebkit
from .webkit_parser_header_fix import HeaderFooterTextWebKitParser


def make_ranges(top, offset):
    """Return sorted days ranges

    :param top: maximum overdue day
    :param offset: offset for ranges

    :returns: list of sorted ranges tuples in days
              eg. [(-100000, 0), (0, offset),
                   (offset, n*offset), ... (top, 100000)]
    """
    ranges = [(n, min(n + offset, top)) for n in xrange(0, top, offset)]
    ranges.insert(0, (-100000000000, 0))
    ranges.append((top, 100000000000))
    return ranges


# list of overdue ranges
RANGES = make_ranges(120, 30)


def make_ranges_titles():
    """Generates title to be used by mako"""
    titles = [_('Not Due')]
    titles += [_(u'Overdue ≤ %s d.') % x[1] for x in RANGES[1:-1]]
    titles.append(_('Overdue > %s d.') % RANGES[-1][0])
    return titles


# list of overdue ranges title
RANGES_TITLES = make_ranges_titles()
# list of payable journal types
REC_PAY_TYPE = ('purchase', 'sale')
# list of refund payable type
REFUND_TYPE = ('purchase_refund', 'sale_refund')
INV_TYPE = REC_PAY_TYPE + REFUND_TYPE


class AccountAgedTrialBalanceWebkit(PartnersOpenInvoicesWebkit):

    """Compute Aged Partner Balance based on result of Open Invoices"""

    # pylint: disable=old-api7-method-defined
    def __init__(self, cursor, uid, name, context=None):
        """Constructor,
           refer to :class:`openerp.report.report_sxw.rml_parse`"""
        super(AccountAgedTrialBalanceWebkit, self).__init__(cursor, uid, name,
                                                            context=context)
        self.pool = RegistryManager.get(self.cr.dbname)
        self.cursor = self.cr
        company = self.pool.get('res.users').browse(self.cr, uid, uid,
                                                    context=context).company_id

        header_report_name = ' - '.join((_('Aged Partner Balance'),
                                         company.currency_id.name))

        footer_date_time = self.formatLang(str(datetime.today()),
                                           date_time=True)

        self.localcontext.update({
            'cr': cursor,
            'uid': uid,
            'company': company,
            'ranges': self._get_ranges(),
            'ranges_titles': self._get_ranges_titles(),
            'report_name': _('Aged Partner Balance'),
            'additional_args': [
                ('--header-font-name', 'Helvetica'),
                ('--footer-font-name', 'Helvetica'),
                ('--header-font-size', '10'),
                ('--footer-font-size', '6'),
                ('--header-left', header_report_name),
                ('--header-spacing', '2'),
                ('--footer-left', footer_date_time),
                ('--footer-right',
                 ' '.join((_('Page'), '[page]', _('of'), '[topage]'))),
                ('--footer-line',),
            ],
        })

    def _get_ranges(self):
        """:returns: :cons:`RANGES`"""
        return RANGES

    def _get_ranges_titles(self):
        """:returns: :cons: `RANGES_TITLES`"""
        return RANGES_TITLES

    def set_context(self, objects, data, ids, report_type=None):
        """Populate aged_lines, aged_balance, aged_percents attributes

        on each account browse record that will be used by mako template
        The browse record are store in :attr:`objects`

        The computation are based on the ledger_lines attribute set on account
        contained by :attr:`objects`

        :attr:`objects` values were previously set by parent class
        :class: `.open_invoices.PartnersOpenInvoicesWebkit`

        :returns: parent :class:`.open_invoices.PartnersOpenInvoicesWebkit`
                  call to set_context

        """

        res = super(AccountAgedTrialBalanceWebkit, self).set_context(
            objects,
            data,
            ids,
            report_type=report_type
        )

        agged_lines_accounts = {}
        agged_totals_accounts = {}
        agged_percents_accounts = {}

        for acc in self.objects:
            agged_lines_accounts[acc.id] = {}
            agged_totals_accounts[acc.id] = {}
            agged_percents_accounts[acc.id] = {}

            for part_id, partner_lines in\
                    self.localcontext['ledger_lines'][acc.id].items():

                aged_lines = self.compute_aged_lines(part_id,
                                                     partner_lines,
                                                     data)
                if aged_lines:
                    agged_lines_accounts[acc.id][part_id] = aged_lines
            agged_totals_accounts[acc.id] = totals = self.compute_totals(
                agged_lines_accounts[acc.id].values())
            agged_percents_accounts[acc.id] = self.compute_percents(totals)

        self.localcontext.update({
            'agged_lines_accounts': agged_lines_accounts,
            'agged_totals_accounts': agged_totals_accounts,
            'agged_percents_accounts': agged_percents_accounts,
        })

        # Free some memory
        del(self.localcontext['ledger_lines'])
        return res

    def compute_aged_lines(self, partner_id, ledger_lines, data):
        """Add property aged_lines to accounts browse records

        contained in :attr:`objects` for a given partner

        :param: partner_id: current partner
        :param ledger_lines: generated by parent
                 :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :returns: dict of computed aged lines
                  eg {'balance': 1000.0,
                       'aged_lines': {(90, 120): 0.0, ...}

        """
        lines_to_age = self.filter_lines(partner_id, ledger_lines)
        res = {}
        end_date = self._get_end_date(data)
        aged_lines = dict.fromkeys(RANGES, 0.0)
        reconcile_lookup = self.get_reconcile_count_lookup(lines_to_age)
        res['aged_lines'] = aged_lines
        for line in lines_to_age:
            compute_method = self.get_compute_method(reconcile_lookup,
                                                     partner_id,
                                                     line)
            delay = compute_method(line, end_date, ledger_lines)
            classification = self.classify_line(partner_id, delay)
            aged_lines[classification] += line['debit'] - line['credit']
        self.compute_balance(res, aged_lines)
        return res

    def _get_end_date(self, data):
        """Retrieve end date to be used to compute delay.

        :param data: data dict send to report contains form dict

        :returns: end date to be used to compute overdue delay

        """
        end_date = None
        date_to = data['form']['date_to']
        period_to_id = data['form']['period_to']
        fiscal_to_id = data['form']['fiscalyear_id']
        if date_to:
            end_date = date_to
        elif period_to_id:
            period_to = self.pool['account.period'].browse(self.cr,
                                                           self.uid,
                                                           period_to_id)
            end_date = period_to.date_stop
        elif fiscal_to_id:
            fiscal_to = self.pool['account.fiscalyear'].browse(self.cr,
                                                               self.uid,
                                                               fiscal_to_id)
            end_date = fiscal_to.date_stop
        else:
            raise ValueError('End date and end period not available')
        return end_date

    def _compute_delay_from_key(self, key, line, end_date):
        """Compute overdue delay delta in days for line using attribute in key

        delta = end_date - date of key

        :param line: current ledger line
        :param key: date key to be used to compute delta
        :param end_date: end_date computed for wizard data

        :returns: delta in days
        """
        from_date = datetime.strptime(line[key], DEFAULT_SERVER_DATE_FORMAT)
        end_date = datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT)
        delta = end_date - from_date
        return delta.days

    def compute_delay_from_maturity(self, line, end_date, ledger_lines):
        """Compute overdue delay delta in days for line using attribute in key

        delta = end_date - maturity date

        :param line: current ledger line
        :param end_date: end_date computed for wizard data
        :param ledger_lines: generated by parent
                 :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :returns: delta in days
        """
        return self._compute_delay_from_key('date_maturity',
                                            line,
                                            end_date)

    def compute_delay_from_date(self, line, end_date, ledger_lines):
        """Compute overdue delay delta in days for line using attribute in key

        delta = end_date - date

        :param line: current ledger line
        :param end_date: end_date computed for wizard data
        :param ledger_lines: generated by parent
                 :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :returns: delta in days
        """
        return self._compute_delay_from_key('ldate',
                                            line,
                                            end_date)

    def compute_delay_from_partial_rec(self, line, end_date, ledger_lines):
        """Compute overdue delay delta in days for the case where move line

        is related to a partial reconcile with more than one reconcile line

        :param line: current ledger line
        :param end_date: end_date computed for wizard data
        :param ledger_lines: generated by parent
                 :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :returns: delta in days
        """
        sale_lines = [
            x for x in ledger_lines if x['jtype'] in REC_PAY_TYPE and
            line['rec_id'] == x['rec_id']
        ]
        refund_lines = [
            x for x in ledger_lines if x['jtype'] in REFUND_TYPE and
            line['rec_id'] == x['rec_id']
        ]
        if len(sale_lines) == 1:
            reference_line = sale_lines[0]
        elif len(refund_lines) == 1:
            reference_line = refund_lines[0]
        else:
            reference_line = line
        key = 'date_maturity' if reference_line.get(
            'date_maturity') else 'ldate'
        return self._compute_delay_from_key(key,
                                            reference_line,
                                            end_date)

    def get_compute_method(self, reconcile_lookup, partner_id, line):
        """Get the function that should compute the delay for a given line

        :param reconcile_lookup: dict of reconcile group by id and count
                                 {rec_id: count of line related to reconcile}
        :param partner_id: current partner_id
        :param line: current ledger line generated by parent
                     :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :returns: function bounded to :class:`.AccountAgedTrialBalanceWebkit`

        """
        if reconcile_lookup.get(line['rec_id'], 0.0) > 1:
            return self.compute_delay_from_partial_rec
        elif line['jtype'] in INV_TYPE and line.get('date_maturity'):
            return self.compute_delay_from_maturity
        else:
            return self.compute_delay_from_date

    def line_is_valid(self, partner_id, line):
        """Predicate hook that allows to filter line to be treated

        :param partner_id: current partner_id
        :param line: current ledger line generated by parent
                     :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :returns: boolean True if line is allowed
        """
        return True

    def filter_lines(self, partner_id, lines):
        """Filter ledger lines that have to be treated

        :param partner_id: current partner_id
        :param lines: ledger_lines related to current partner
                      and generated by parent
                      :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :returns: list of allowed lines

        """
        return [x for x in lines if self.line_is_valid(partner_id, x)]

    def classify_line(self, partner_id, overdue_days):
        """Return the overdue range for a given delay

        We loop from smaller range to higher
        This should be the most effective solution as generaly
        customer tend to have one or two month of delay

        :param overdue_days: delay in days
        :param partner_id: current partner_id

        :returns: the correct range in :const:`RANGES`

        """
        for drange in RANGES:
            if overdue_days <= drange[1]:
                return drange
        return drange

    def compute_balance(self, res, aged_lines):
        """Compute the total balance of aged line
        for given account"""
        res['balance'] = sum(aged_lines.values())

    def compute_totals(self, aged_lines):
        """Compute the totals for an account

        :param aged_lines: dict of aged line taken from the
                           property added to account record

        :returns: dict of total {'balance':1000.00, (30, 60): 3000,...}

        """
        totals = {}
        totals['balance'] = sum(x.get('balance', 0.0) for
                                x in aged_lines)
        aged_ranges = [x.get('aged_lines', {}) for x in aged_lines]
        for drange in RANGES:
            totals[drange] = sum(x.get(drange, 0.0) for x in aged_ranges)
        return totals

    def compute_percents(self, totals):
        percents = {}
        base = totals['balance'] or 1.0
        for drange in RANGES:
            percents[drange] = (totals[drange] / base) * 100.0
        return percents

    def get_reconcile_count_lookup(self, lines):
        """Compute an lookup dict

        It contains has partial reconcile id as key and the count of lines
        related to the reconcile id

        :param: a list of ledger lines generated by parent
                :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :retuns: lookup dict {ṛec_id: count}

        """
        # possible bang if l_ids is really long.
        # We have the same weakness in common_report ...
        # but it seems not really possible for a partner
        # So I'll keep that option.
        l_ids = tuple(x['id'] for x in lines)
        sql = ("SELECT reconcile_partial_id, COUNT(*) FROM account_move_line"
               "   WHERE reconcile_partial_id IS NOT NULL"
               "   AND id in %s"
               "   GROUP BY reconcile_partial_id")
        self.cr.execute(sql, (l_ids,))
        res = self.cr.fetchall()
        return dict((x[0], x[1]) for x in res)


HeaderFooterTextWebKitParser(
    'report.account.account_aged_trial_balance_webkit',
    'account.account',
    'addons/account_financial_report_webkit/report/templates/\
                                                    aged_trial_webkit.mako',
    parser=AccountAgedTrialBalanceWebkit,
)
