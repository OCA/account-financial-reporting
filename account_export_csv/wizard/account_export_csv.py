# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Joel Grand-Guillaume and Vincent Renaville Copyright 2013
#    Camptocamp SA
#    CSV data formating inspired from
# http://docs.python.org/2.7/library/csv.html?highlight=csv#examples
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

import itertools
import tempfile
import StringIO
import cStringIO
import base64

import csv
import codecs

from openerp.osv import orm, fields
from openerp.tools.translate import _


class AccountUnicodeWriter(object):

    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        # created a writer with Excel formating settings
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        # we ensure that we do not try to encode none or bool
        row = (x or u'' for x in row)

        encoded_row = [
            c.encode("utf-8") if isinstance(c, unicode) else c for c in row]

        self.writer.writerow(encoded_row)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class AccountCSVExport(orm.TransientModel):
    _name = 'account.csv.export'
    _description = 'Export Accounting'

    _columns = {
        'data': fields.binary('CSV', readonly=True),
        'company_id': fields.many2one('res.company', 'Company',
                                      invisible=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscalyear',
                                         required=True),
        'periods': fields.many2many(
            'account.period', 'rel_wizard_period',
            'wizard_id', 'period_id', 'Periods',
            help='All periods in the fiscal year if empty'),
        'journal_ids': fields.many2many(
            'account.journal',
            'rel_wizard_journal',
            'wizard_id',
            'journal_id',
            'Journals',
            help='If empty, use all journals, only used for journal entries'),
        'account_ids': fields.many2many(
            'account.account',
            'rel_wizard_account',
            'wizard_id',
            'account_id',
            'Accounts',
            help='If empty, use all accounts, only used for journal entries'),
        'export_filename': fields.char('Export CSV Filename', size=128),
    }

    def _get_company_default(self, cr, uid, context=None):
        comp_obj = self.pool['res.company']
        return comp_obj._company_default_get(cr, uid, 'account.fiscalyear',
                                             context=context)

    def _get_fiscalyear_default(self, cr, uid, context=None):
        fiscalyear_obj = self.pool['account.fiscalyear']
        context['company_id'] = self._get_company_default(cr, uid, context)
        return fiscalyear_obj.find(cr, uid, dt=None, exception=True,
                                   context=context)

    _defaults = {'company_id': _get_company_default,
                 'fiscalyear_id': _get_fiscalyear_default,
                 'export_filename': 'account_export.csv'}

    def action_manual_export_account(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        rows = self.get_data(cr, uid, ids, "account", context)
        file_data = StringIO.StringIO()
        try:
            writer = AccountUnicodeWriter(file_data)
            writer.writerows(rows)
            file_value = file_data.getvalue()
            self.write(cr, uid, ids,
                       {'data': base64.encodestring(file_value)},
                       context=context)
        finally:
            file_data.close()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.csv.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _get_header_account(self, cr, uid, ids, context=None):
        return [_(u'CODE'),
                _(u'NAME'),
                _(u'DEBIT'),
                _(u'CREDIT'),
                _(u'BALANCE'),
                ]

    def _get_rows_account(self, cr, uid, ids,
                          fiscalyear_id,
                          period_range_ids,
                          journal_ids,
                          account_ids,
                          context=None):
        """
        Return list to generate rows of the CSV file
        """
        cr.execute("""
                select ac.code,ac.name,
                sum(debit) as sum_debit,
                sum(credit) as sum_credit,
                sum(debit) - sum(credit) as balance
                from account_move_line as aml,account_account as ac
                where aml.account_id = ac.id
                and period_id in %(period_ids)s
                group by ac.id,ac.code,ac.name
                order by ac.code
                   """,
                   {'fiscalyear_id': fiscalyear_id,
                       'period_ids': tuple(period_range_ids)}
                   )
        res = cr.fetchall()

        rows = []
        for line in res:
            rows.append(list(line))
        return rows

    def action_manual_export_analytic(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        rows = self.get_data(cr, uid, ids, "analytic", context)
        file_data = StringIO.StringIO()
        try:
            writer = AccountUnicodeWriter(file_data)
            writer.writerows(rows)
            file_value = file_data.getvalue()
            self.write(cr, uid, ids,
                       {'data': base64.encodestring(file_value)},
                       context=context)
        finally:
            file_data.close()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.csv.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _get_header_analytic(self, cr, uid, ids, context=None):
        return [_(u'ANALYTIC CODE'),
                _(u'ANALYTIC NAME'),
                _(u'CODE'),
                _(u'ACCOUNT NAME'),
                _(u'DEBIT'),
                _(u'CREDIT'),
                _(u'BALANCE'),
                ]

    def _get_rows_analytic(self, cr, uid, ids,
                           fiscalyear_id,
                           period_range_ids,
                           journal_ids,
                           account_ids,
                           context=None):
        """
        Return list to generate rows of the CSV file
        """
        cr.execute("""  select aac.code as analytic_code,
                        aac.name as analytic_name,
                        ac.code,ac.name,
                        sum(debit) as sum_debit,
                        sum(credit) as sum_credit,
                        sum(debit) - sum(credit) as balance
                        from account_move_line
                        left outer join account_analytic_account as aac
                        on (account_move_line.analytic_account_id = aac.id)
                        inner join account_account as ac
                        on account_move_line.account_id = ac.id
                        and account_move_line.period_id in %(period_ids)s
                        group by aac.id,aac.code,aac.name,ac.id,ac.code,ac.name
                        order by aac.code
                   """,
                   {'fiscalyear_id': fiscalyear_id,
                       'period_ids': tuple(period_range_ids)}
                   )
        res = cr.fetchall()

        rows = []
        for line in res:
            rows.append(list(line))
        return rows

    def action_manual_export_journal_entries(self, cr, uid, ids, context=None):
        """
        Here we use TemporaryFile to avoid full filling the OpenERP worker
        Memory
        We also write the data to the wizard with SQL query as write seams
        to use too much memory as well.

        Those improvements permitted to improve the export from a 100k line to
        200k lines
        with default `limit_memory_hard = 805306368` (768MB) with more lines,
        you might encounter a MemoryError when trying to download the file even
        if it has been generated.

        To be able to export bigger volume of data, it is advised to set
        limit_memory_hard to 2097152000 (2 GB) to generate the file and let
        OpenERP load it in the wizard when trying to download it.

        Tested with up to a generation of 700k entry lines
        """
        this = self.browse(cr, uid, ids)[0]
        rows = self.get_data(cr, uid, ids, "journal_entries", context)
        with tempfile.TemporaryFile() as file_data:
            writer = AccountUnicodeWriter(file_data)
            writer.writerows(rows)
            with tempfile.TemporaryFile() as base64_data:
                file_data.seek(0)
                base64.encode(file_data, base64_data)
                base64_data.seek(0)
                cr.execute("""
                UPDATE account_csv_export
                SET data = %s
                WHERE id = %s""", (base64_data.read(), ids[0]))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.csv.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _get_header_journal_entries(self, cr, uid, ids, context=None):
        return [
            # Standard Sage export fields
            _(u'DATE'),
            _(u'JOURNAL CODE'),
            _(u'ACCOUNT CODE'),
            _(u'PARTNER NAME'),
            _(u'REF'),
            _(u'DESCRIPTION'),
            _(u'DEBIT'),
            _(u'CREDIT'),
            _(u'FULL RECONCILE'),
            _(u'PARTIAL RECONCILE'),
            _(u'ANALYTIC ACCOUNT CODE'),

            # Other fields
            _(u'ENTRY NUMBER'),
            _(u'ACCOUNT NAME'),
            _(u'BALANCE'),
            _(u'AMOUNT CURRENCY'),
            _(u'CURRENCY'),
            _(u'ANALYTIC ACCOUNT NAME'),
            _(u'JOURNAL'),
            _(u'MONTH'),
            _(u'FISCAL YEAR'),
            _(u'TAX CODE CODE'),
            _(u'TAX CODE NAME'),
            _(u'TAX AMOUNT'),
            _(u'BANK STATEMENT'),
        ]

    def _get_rows_journal_entries(self, cr, uid, ids,
                                  fiscalyear_id,
                                  period_range_ids,
                                  journal_ids,
                                  account_ids,
                                  context=None):
        """
        Create a generator of rows of the CSV file
        """
        cr.execute("""
        SELECT
          account_move_line.date AS date,
          account_journal.name as journal,
          account_account.code AS account_code,
          res_partner.name AS partner_name,
          account_move_line.ref AS ref,
          account_move_line.name AS description,
          account_move_line.debit AS debit,
          account_move_line.credit AS credit,
          account_move_reconcile.name as full_reconcile,
          account_move_line.reconcile_partial_id AS partial_reconcile_id,
          account_analytic_account.code AS analytic_account_code,
          account_move.name AS entry_number,
          account_account.name AS account_name,
          account_move_line.debit - account_move_line.credit AS balance,
          account_move_line.amount_currency AS amount_currency,
          res_currency.name AS currency,
          account_analytic_account.name AS analytic_account_name,
          account_journal.name as journal,
          account_period.code AS month,
          account_fiscalyear.name as fiscal_year,
          account_tax_code.code AS aml_tax_code_code,
          account_tax_code.name AS aml_tax_code_name,
          account_move_line.tax_amount AS aml_tax_amount,
          account_bank_statement.name AS bank_statement
        FROM
          public.account_move_line
          JOIN account_account on
            (account_account.id=account_move_line.account_id)
          JOIN account_period on
            (account_period.id=account_move_line.period_id)
          JOIN account_fiscalyear on
            (account_fiscalyear.id=account_period.fiscalyear_id)
          JOIN account_journal on
            (account_journal.id = account_move_line.journal_id)
          LEFT JOIN res_currency on
            (res_currency.id=account_move_line.currency_id)
          LEFT JOIN account_move_reconcile on
            (account_move_reconcile.id = account_move_line.reconcile_id)
          LEFT JOIN res_partner on
            (res_partner.id=account_move_line.partner_id)
          LEFT JOIN account_move on
            (account_move.id=account_move_line.move_id)
          LEFT JOIN account_tax on
            (account_tax.id=account_move_line.account_tax_id)
          LEFT JOIN account_tax_code on
            (account_tax_code.id=account_move_line.tax_code_id)
          LEFT JOIN account_analytic_account on
            (account_analytic_account.id=account_move_line.analytic_account_id)
          LEFT JOIN account_bank_statement on
            (account_bank_statement.id=account_move_line.statement_id)
        WHERE account_period.id IN %(period_ids)s
        AND account_journal.id IN %(journal_ids)s
        AND account_account.id IN %(account_ids)s
        ORDER BY account_move_line.date
        """,
                   {'period_ids': tuple(period_range_ids),
                    'journal_ids': tuple(journal_ids),
                    'account_ids': tuple(account_ids)}
                   )
        while 1:
            # http://initd.org/psycopg/docs/cursor.html#cursor.fetchmany
            # Set cursor.arraysize to minimize network round trips
            cr.arraysize = 100
            rows = cr.fetchmany()
            if not rows:
                break
            for row in rows:
                yield row

    def get_data(self, cr, uid, ids, result_type, context=None):
        get_header_func = getattr(
            self, ("_get_header_%s" % (result_type)), None)
        get_rows_func = getattr(self, ("_get_rows_%s" % (result_type)), None)
        form = self.browse(cr, uid, ids[0], context=context)
        fiscalyear_id = form.fiscalyear_id.id
        if form.periods:
            period_range_ids = [x.id for x in form.periods]
        else:
            # If not period selected , we take all periods
            p_obj = self.pool.get("account.period")
            period_range_ids = p_obj.search(
                cr, uid, [('fiscalyear_id', '=', fiscalyear_id)],
                context=context)
        journal_ids = None
        if form.journal_ids:
            journal_ids = [x.id for x in form.journal_ids]
        else:
            j_obj = self.pool.get("account.journal")
            journal_ids = j_obj.search(cr, uid, [], context=context)
        account_ids = None
        if form.account_ids:
            account_ids = [x.id for x in form.account_ids]
        else:
            aa_obj = self.pool.get("account.account")
            account_ids = aa_obj.search(cr, uid, [], context=context)
        rows = itertools.chain((get_header_func(cr, uid, ids,
                                                context=context),),
                               get_rows_func(cr, uid, ids,
                                             fiscalyear_id,
                                             period_range_ids,
                                             journal_ids,
                                             account_ids,
                                             context=context)
                               )
        return rows
