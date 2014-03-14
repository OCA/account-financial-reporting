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
from datetime import datetime

from openerp import pooler
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from .open_invoices import PartnersOpenInvoicesWebkit
from .webkit_parser_header_fix import HeaderFooterTextWebKitParser


def make_ranges(top, offset):
    """Return sorted day ranges"""
    ranges = [(n, min(n + offset, top)) for n in xrange(0, top, offset)]
    ranges.insert(0, (-100000000000, 0))
    ranges.append((top, 100000000000))
    return ranges

#list of overdue ranges
RANGES = make_ranges(120, 30)


def make_ranges_titles():
    """Generates title to be used by Mako"""
    titles = [_('Due')]
    titles += [_('Overdue since %s d.') % x[1] for x in RANGES[1:-1]]
    titles.append(_('Older'))
    return titles

#list of overdue ranges title
RANGES_TITLES = make_ranges_titles()
#list of payable journal types
REC_PAY_TYPE = ('purchase', 'sale')
#list of refund payable type
REFUND_TYPE = ('purchase_refund', 'sale_refund')
INV_TYPE = REC_PAY_TYPE + REFUND_TYPE


class AccountAgedTrialBalanceWebkit(PartnersOpenInvoicesWebkit):

    def __init__(self, cursor, uid, name, context=None):
        super(AccountAgedTrialBalanceWebkit, self).__init__(cursor, uid, name,
                                                            context=context)
        self.pool = pooler.get_pool(self.cr.dbname)
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
                ('--footer-right', ' '.join((_('Page'), '[page]', _('of'), '[topage]'))),
                ('--footer-line',),
            ],
        })

    def _get_ranges(self):
        return RANGES

    def _get_ranges_titles(self):
        return RANGES_TITLES

    def set_context(self, objects, data, ids, report_type=None):
        """Populate aged_lines, aged_balance, aged_percents attributes
        on each browse record that will be used by mako template
        """
        res = super(AccountAgedTrialBalanceWebkit, self).set_context(
            objects,
            data,
            ids,
            report_type=report_type
        )

        for acc in self.objects:
            acc.aged_lines = {}
            acc.agged_totals = {}
            acc.agged_percents = {}
            for part_id, partner_lines in acc.ledger_lines.items():
                aged_lines = self.compute_aged_lines(part_id,
                                                     partner_lines,
                                                     data)
                if aged_lines:
                    acc.aged_lines[part_id] = aged_lines
            acc.aged_totals = totals = self.compute_totals(acc.aged_lines.values())
            acc.aged_percents = self.compute_percents(totals)
        #Free some memory
        del(acc.ledger_lines)
        return res

    def compute_aged_lines(self, partner_id, lines, data):
        lines_to_age = self.filter_lines(partner_id, lines)
        res = {}
        period_to_id = data['form']['period_to']

        period_to = self.pool['account.period'].browse(self.cr,
                                                       self.uid,
                                                       period_to_id)
        end_date = period_to.date_stop
        aged_lines = dict.fromkeys(RANGES, 0.0)
        reconcile_lookup = self.get_reconcile_count_lookup(lines_to_age)
        res['aged_lines'] = aged_lines
        for line in lines_to_age:
            compute_method = self.get_compute_method(reconcile_lookup,
                                                     partner_id,
                                                     line)
            delay = compute_method(line, end_date)
            classification = self.classify_line(partner_id, delay)
            aged_lines[classification] += line['debit'] - line['credit']
        self.compute_balance(res, aged_lines)
        return res

    def _compute_delay_from_key(self, key, line, end_date):
        from_date = datetime.strptime(line[key], DEFAULT_SERVER_DATE_FORMAT)
        end_date = datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT)
        delta = end_date - from_date
        return delta.days

    def compute_delay_from_maturity(self, line, end_date):
        return self._compute_delay_from_key('date_maturity',
                                            line,
                                            end_date)

    def compute_delay_from_date(self, line, end_date):
        return self._compute_delay_from_key('date',
                                            line,
                                            end_date)

    def compute_delay_from_partial_rec(self, line, end_date):
        return 25

    def get_compute_method(self, reconcile_lookup, partner_id, line):
        if reconcile_lookup.get(line['rec_id'], 0.0) > 1:
            return self.compute_delay_from_partial_rec
        if line['jtype'] in INV_TYPE:
            if line.get('date_maturity'):
                return self.compute_delay_from_maturity
            return self.compute_delay_from_date
        else:
            return self.compute_delay_from_date

    def line_is_valid(self, partner_id, line):
        """Predicate that tells if line has to be treated"""
        # waiting some spec here maybe dead code
        return True

    def filter_lines(self, partner_id, lines):
        # vaiting specs
        return [x for x in lines if self.line_is_valid(partner_id, x)]

    def classify_line(self, partner_id, overdue_days):
        """Return the range index for a number of overdue days

        We loop from smaller range to higher
        This should be the most effective solution as generaly
        customer tend to have one or two month of delay

        :param overdue_days: int representing the lenght in days of delay
        :returns: the index of the correct range in ´´RANGES´´
        """
        for drange in RANGES:
            if overdue_days <= drange[1]:
                return drange
        return drange

    def compute_balance(self, res, aged_lines):
        res['balance'] = sum(aged_lines.values())

    def compute_totals(self, aged_lines):
        totals = {}
        totals['balance'] = sum(x.get('balance', 0.0) for
                                x in aged_lines)
        aged_ranges = [x.get('aged_lines', {}) for x in aged_lines]
        for drange in RANGES:
            totals[drange] = sum(x.get(drange, 0.0) for x in aged_ranges)
        print totals
        return totals

    def compute_percents(self, totals):
        percents = {}
        base = float(totals['balance']) or 1.0
        for drange in RANGES:
            percents[drange] = (float(totals[drange]) / base) * 100.0
        print percents
        return percents

    def get_reconcile_count_lookup(self, lines):
        # possible bang if l_ids is really long.
        # We have the same weakness in common_report ...
        # but it seems not really possible for a partner
        # So I'll keep that option.
        l_ids = tuple(x['id'] for x in lines)
        sql = ("SELECT reconcile_partial_id, COUNT(*) FROM account_move_line \n"
               "   WHERE reconcile_partial_id IS NOT NULL \n"
               "   AND id in %s \n"
               "   GROUP BY reconcile_partial_id")
        self.cr.execute(sql, (l_ids,))
        res = self.cr.fetchall()
        if res:
            return dict((x[0], x[1]) for x in res)
        return {}

HeaderFooterTextWebKitParser(
    'report.account.account_aged_trial_balance_webkit',
    'account.account',
    'addons/account_financial_report_webkit/report/templates/aged_trial_webkit.mako',
    parser=AccountAgedTrialBalanceWebkit,
)
