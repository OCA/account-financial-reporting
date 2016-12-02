# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from openerp.report import report_sxw
from openerp.tools.translate import translate
import logging
_logger = logging.getLogger(__name__)

_ir_translation_name = 'nov.account.journal.print'


class nov_journal_print(report_sxw.rml_parse):

    def set_context(self, objects, data, ids, report_type=None):
        # _logger.warn('set_context, objects = %s, data = %s,
        # ids = %s', objects, data, ids)
        super(nov_journal_print, self).set_context(objects, data, ids)
        j_obj = self.pool.get('account.journal')
        p_obj = self.pool.get('account.period')
        fy_obj = self.pool.get('account.fiscalyear')
        self.sort_selection = data['sort_selection']
        if data['target_move'] == 'posted':
            self.move_states = ['posted']
        else:
            self.move_states = ['draft', 'posted']
        self.display_currency = self.localcontext[
            'display_currency'] = data['display_currency']
        self.group_entries = data['group_entries']
        self.print_by = data['print_by']
        self.report_type = report_type
        if self.print_by == 'period':
            journal_period_ids = data['journal_period_ids']
            objects = []
            for jp in journal_period_ids:
                journal = j_obj.browse(self.cr, self.uid, jp[0], self.context)
                periods = p_obj.browse(self.cr, self.uid, jp[1], self.context)
                objects.extend([(journal, period) for period in periods])
                self.localcontext['objects'] = self.objects = objects
        else:
            journal_fy_ids = data['journal_fy_ids']
            objects = []
            for jf in journal_fy_ids:
                journal = j_obj.browse(self.cr, self.uid, jf[0], self.context)
                fiscalyear = fy_obj.browse(
                    self.cr, self.uid, jf[1], self.context)
                objects.append((journal, fiscalyear))
                self.localcontext['objects'] = self.objects = objects

    def __init__(self, cr, uid, name, context):
        if context is None:
            context = {}
        super(nov_journal_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'title': self._title,
            'amount_title': self._amount_title,
            'lines': self._lines,
            'sum1': self._sum1,
            'sum2': self._sum2,
            'tax_codes': self._tax_codes,
            'sum_vat': self._sum_vat,
            '_': self._,
        })
        self.context = context

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(self.cr, _ir_translation_name, 'report', lang, src) \
            or src

    def _title(self, object):
        return ((self.print_by == 'period' and self._('Period') or
                 self._('Fiscal Year')) + ' ' + object[1].name, object[0].name)

    def _amount_title(self):
        return self.display_currency and \
            (self._('Amount'), self._('Currency')) or (
                self._('Debit'), self._('Credit'))

    def _lines(self, object):
        j_obj = self.pool['account.journal']
        _ = self._
        journal = object[0]
        journal_id = journal.id
        if self.print_by == 'period':
            period = object[1]
            period_id = period.id
            period_ids = [period_id]
            # update status period
            ids_journal_period = self.pool['account.journal.period'].\
                search(self.cr, self.uid, [('journal_id', '=', journal_id),
                                           ('period_id', '=', period_id)])
            if ids_journal_period:
                self.cr.execute(
                    '''update account_journal_period set state=%s
                    where journal_id=%s and period_id=%s and state=%s''',
                    ('printed', journal_id, period_id, 'draft'))
            else:
                self.pool.get('account.journal.period').create(
                    self.cr, self.uid,
                    {'name': (journal.code or journal.name) + ':' +
                             (period.name or ''),
                        'journal_id': journal.id,
                        'period_id': period.id,
                        'state': 'printed',
                     })
                _logger.error("""The Entry for Period '%s', Journal '%s' was
                missing in 'account.journal.period' and
                has been fixed now !""",
                              period.name, journal.name)
        else:
            fiscalyear = object[1]
            period_ids = [x.id for x in fiscalyear.period_ids]

        select_extra, join_extra, where_extra = j_obj._report_xls_query_extra(
            self.cr, self.uid, self.context)

        # SQL select for performance reasons, as a consequence, there are no
        # field value translations.
        # If performance is no issue, you can adapt the _report_xls_template in
        # an inherited module to add field value translations.
        self.cr.execute("SELECT l.move_id AS move_id, l.id AS aml_id, "
                        "am.name AS move_name, "
                        "coalesce(am.ref,'') AS move_ref, "
                        "am.date AS move_date, "
                        "aa.id AS account_id, aa.code AS acc_code, "
                        "aa.name AS acc_name, "
                        "aj.name AS journal, aj.code AS journal_code, "
                        "coalesce(rp.name,'') AS partner_name, "
                        "coalesce(rp.ref,'') AS partner_ref, "
                        "rp.id AS partner_id, "
                        "coalesce(l.name,'') AS aml_name, "
                        "l.date_maturity AS date_maturity, "
                        "coalesce(ap.code, ap.name) AS period, "
                        "coalesce(atc.code,'') AS tax_code, "
                        "atc.id AS tax_code_id, "
                        "coalesce(l.tax_amount,0.0) AS tax_amount, "
                        "coalesce(l.debit,0.0) AS debit, "
                        "coalesce(l.credit,0.0) AS credit, "
                        "coalesce(amr.name,'') AS reconcile, "
                        "coalesce(amrp.name,'') AS reconcile_partial, "
                        "ana.name AS an_acc_name, "
                        "coalesce(ana.code,'') AS an_acc_code, "
                        "coalesce(l.amount_currency,0.0) AS amount_currency, "
                        "rc.id AS currency_id, rc.name AS currency_name, "
                        "rc.symbol AS currency_symbol, "
                        "coalesce(ai.internal_number,'-') AS inv_number, "
                        "coalesce(abs.name,'-') AS st_number, "
                        "coalesce(av.number,'-') AS voucher_number " +
                        select_extra +
                        "FROM account_move_line l "
                        "INNER JOIN account_move am ON l.move_id = am.id "
                        "INNER JOIN account_account aa "
                        "ON l.account_id = aa.id "
                        "INNER JOIN account_journal aj "
                        "ON l.journal_id = aj.id "
                        "INNER JOIN account_period ap ON l.period_id = ap.id "
                        "LEFT OUTER JOIN account_invoice ai "
                        "ON ai.move_id = am.id "
                        "LEFT OUTER JOIN account_voucher av "
                        "ON av.move_id = am.id "
                        "LEFT OUTER JOIN account_bank_statement abs "
                        "ON l.statement_id = abs.id "
                        "LEFT OUTER JOIN res_partner rp "
                        "ON l.partner_id = rp.id "
                        "LEFT OUTER JOIN account_tax_code atc "
                        "ON l.tax_code_id = atc.id  "
                        "LEFT OUTER JOIN account_move_reconcile amr "
                        "ON l.reconcile_id = amr.id  "
                        "LEFT OUTER JOIN account_move_reconcile amrp "
                        "ON l.reconcile_partial_id = amrp.id  "
                        "LEFT OUTER JOIN account_analytic_account ana "
                        "ON l.analytic_account_id = ana.id  "
                        "LEFT OUTER JOIN res_currency rc "
                        "ON l.currency_id = rc.id  " + join_extra +
                        "WHERE l.period_id IN %s AND l.journal_id = %s "
                        "AND am.state IN %s " + where_extra +
                        "ORDER BY " + self.sort_selection +
                        ", move_date, move_id, acc_code",
                        (tuple(period_ids), journal_id,
                         tuple(self.move_states)))
        lines = self.cr.dictfetchall()

        # add reference of corresponding origin document
        if journal.type in ('sale', 'sale_refund', 'purchase',
                            'purchase_refund'):
            [x.update({'docname': (_('Invoice') + ': ' + x['inv_number']) or
                       (_('Voucher') + ': ' + x['voucher_number']) or '-'})
             for x in lines]
        elif journal.type in ('bank', 'cash'):
            [x.update({'docname': (_('Statement') + ': ' + x['st_number']) or
                       (_('Voucher') + ': ' + x['voucher_number']) or '-'})
             for x in lines]
        else:
            code_string = j_obj._report_xls_document_extra(
                self.cr, self.uid, self.context)
            # _logger.warn('code_string= %s', code_string)
            # disable=W0123, safe_eval doesn't apply here since
            # code_string comes from python module
            [x.update(
             {'docname': eval(code_string) or '-'})  # pylint: disable=W0123
             for x in lines]

        # group lines
        if self.group_entries:
            lines = self._group_lines(lines)

        # format debit, credit, amount_currency for pdf report
        if self.display_currency and self.report_type == 'pdf':
            curr_obj = self.pool.get('res.currency')
            [x.update({
                'amount1': self.formatLang(x['debit'] - x['credit']),
                'amount2': self.formatLang(
                    x['amount_currency'], monetary=True,
                    currency_obj=curr_obj.browse(self.cr,
                                                 self.uid, x['currency_id'])),
            }) for x in lines]
        else:
            [x.update({'amount1': self.formatLang(x['debit']),
                       'amount2': self.formatLang(x['credit'])})
             for x in lines]

        # insert a flag in every move_line to indicate the end of a move
        # this flag will be used to draw a full line between moves
        for cnt in range(len(lines) - 1):
            if lines[cnt]['move_id'] != lines[cnt + 1]['move_id']:
                lines[cnt]['draw_line'] = 1
            else:
                lines[cnt]['draw_line'] = 0
        lines[-1]['draw_line'] = 1

        return lines

    def _group_lines(self, lines_in):

        _ = self._

        def group_move(lines_in):
            if len(lines_in) == 1:
                return lines_in
            lines_grouped = {}
            for line in lines_in:
                key = (line['account_id'],
                       line['tax_code_id'],
                       line['partner_id'])
                if key not in lines_grouped:
                    lines_grouped[key] = line
                else:
                    lines_grouped[key]['debit'] += line['debit']
                    lines_grouped[key]['credit'] += line['credit']
                    lines_grouped[key]['tax_amount'] += line['tax_amount']
                    lines_grouped[key]['aml_name'] = _('Grouped Entries')
            lines_out = lines_grouped.values()
            lines_out.sort(key=lambda x: x['acc_code'])
            return lines_out

        lines_out = []
        grouped_lines = [lines_in[0]]
        move_id = lines_in[0]['move_id']
        line_cnt = len(lines_in)
        for i in range(1, line_cnt):
            line = lines_in[i]
            if line['move_id'] == move_id:
                grouped_lines.append(line)
                if i == line_cnt - 1:
                    lines_out += group_move(grouped_lines)
            else:
                lines_out += group_move(grouped_lines)
                grouped_lines = [line]
                move_id = line['move_id']

        return lines_out

    def _tax_codes(self, object):
        journal_id = object[0].id
        if self.print_by == 'period':
            period_id = object[1].id
            period_ids = [period_id]
        else:
            fiscalyear = object[1]
            period_ids = [x.id for x in fiscalyear.period_ids]
        self.cr.execute(
            "SELECT distinct tax_code_id FROM account_move_line l "
            "INNER JOIN account_move am ON l.move_id = am.id "
            "WHERE l.period_id in %s AND l.journal_id=%s "
            "AND l.tax_code_id IS NOT NULL AND am.state IN %s",
            (tuple(period_ids), journal_id, tuple(self.move_states)))
        ids = map(lambda x: x[0], self.cr.fetchall())
        if ids:
            self.cr.execute(
                'SELECT id FROM account_tax_code WHERE id IN %s ORDER BY code',
                (tuple(ids),))
            tax_code_ids = map(lambda x: x[0], self.cr.fetchall())
        else:
            tax_code_ids = []
        tax_codes = self.pool.get('account.tax.code').browse(
            self.cr, self.uid, tax_code_ids, self.context)
        return tax_codes

    def _totals(self, field, object, tax_code_id=None):
        journal_id = object[0].id
        if self.print_by == 'period':
            period_id = object[1].id
            period_ids = [period_id]
        else:
            fiscalyear = object[1]
            period_ids = [x.id for x in fiscalyear.period_ids]
        select = "SELECT sum(" + field + ") FROM account_move_line l " \
            "INNER JOIN account_move am ON l.move_id = am.id " \
            "WHERE l.period_id IN %s AND l.journal_id=%s AND am.state IN %s"
        if field == 'tax_amount':
            select += " AND tax_code_id=%s" % tax_code_id
        self.cr.execute(
            select, (tuple(period_ids), journal_id, tuple(self.move_states)))
        return self.cr.fetchone()[0] or 0.0

    def _sum1(self, object):
        return self._totals('debit', object)

    def _sum2(self, object):
        if self.display_currency:
            return ''
        else:
            return self._totals('credit', object)

    def _sum_vat(self, object, tax_code):
        return self._totals('tax_amount', object, tax_code.id)

    def formatLang(self, value, digits=None, date=False, date_time=False,
                   grouping=True, monetary=False, dp=False,
                   currency_obj=False):
        if isinstance(value, (float, int)) and not value:
            return ''
        else:
            return super(nov_journal_print, self).formatLang(
                value, digits,
                date, date_time, grouping, monetary, dp, currency_obj)


report_sxw.report_sxw(
    'report.nov.account.journal.print', 'account.journal',
    'addons/account_journal_report_xls/report/nov_account_journal.rml',
    parser=nov_journal_print, header=False)
