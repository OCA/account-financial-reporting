# Copyright 2013 Camptocamp SA
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import itertools
import tempfile
from io import StringIO, BytesIO
import base64

import csv
import codecs

from odoo import api, fields, models, _


class AccountingWriter(object):

    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = StringIO()
        # created a writer with Excel formating settings
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        # we ensure that we do not try to encode none or bool
        row = (x or '' for x in row)
        self.writer.writerow(row)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        # ... and reencode it into the target encoding as BytesIO
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # seek() or truncate() have side effect if not used combinated
        self.queue.truncate(0)
        self.queue.seek(0)
        # https://stackoverflow.com/questions/4330812/how-do-i-clear-a-stringio-object
        # It fails when you use `self.queue = StringIO()` only add one line

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
        # https://docs.python.org/3/library/io.html#io.IOBase.close
        self.queue.close()


class AccountCSVExport(models.TransientModel):
    _name = 'account.csv.export'
    _description = 'Export Accounting'

    data = fields.Binary('CSV', readonly=True)
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', invisible=True,
        default=lambda self: self._get_company_default())
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    date_range_id = fields.Many2one(
        comodel_name='date.range', string='Date range')
    journal_ids = fields.Many2many(
        comodel_name='account.journal', string='Journals',
        default=lambda s: s._get_journal_default(),
        help='If empty, use all journals, only used for journal entries')
    export_filename = fields.Char(
        string='Export CSV Filename', size=128, default='account_export.csv')

    @api.model
    def _get_journal_default(self):
        """ Implements your own default """
        return False

    @api.model
    def _get_company_default(self):
        return self.env.user.company_id

    @api.onchange('date_range_id')
    def _onchange_date_range(self):
        if self.date_range_id:
            self.date_start = self.date_range_id.date_start
            self.date_end = self.date_range_id.date_end

    @api.onchange('date_start', 'date_end')
    def _onchange_dates(self):
        if self.date_range_id:
            if self.date_start != self.date_range_id.date_start or \
                    self.date_end != self.date_range_id.date_end:
                self.date_range_id = False

    def action_manual_export_account(self):
        self.ensure_one()
        rows = self._get_data("account")
        file_data = BytesIO()
        try:
            writer = AccountingWriter(file_data)
            writer.writerows(rows)
            file_value = file_data.getvalue()
            self.write({'data': base64.encodestring(file_value)})
        finally:
            file_data.close()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.csv.export',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _get_header_account(self):
        return [
            _('CODE'),
            _('NAME'),
            _('DEBIT'),
            _('CREDIT'),
            _('BALANCE'),
        ]

    def _get_rows_account(self, journal_ids):
        """
        Return list to generate rows of the CSV file
        """
        self.ensure_one()
        self.env.cr.execute("""
                select ac.code,ac.name,
                sum(debit) as sum_debit,
                sum(credit) as sum_credit,
                sum(debit) - sum(credit) as balance
                from account_move_line as aml,account_account as ac
                where aml.account_id = ac.id
                AND aml.date >= %(date_start)s
                AND aml.date <= %(date_end)s
                group by ac.id,ac.code,ac.name
                order by ac.code
                   """, {'date_start': self.date_start,
                         'date_end': self.date_end})
        res = self.env.cr.fetchall()

        rows = []
        for line in res:
            rows.append(list(line))
        return rows

    def action_manual_export_analytic(self):
        self.ensure_one()
        rows = self._get_data("analytic")
        file_data = BytesIO()
        try:
            writer = AccountingWriter(file_data)
            writer.writerows(rows)
            file_value = file_data.getvalue()
            self.write({'data': base64.encodestring(file_value)})
        finally:
            file_data.close()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.csv.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _get_header_analytic(self):
        return [
            _('ANALYTIC CODE'),
            _('ANALYTIC NAME'),
            _('CODE'),
            _('ACCOUNT NAME'),
            _('DEBIT'),
            _('CREDIT'),
            _('BALANCE'),
        ]

    def _get_rows_analytic(self, journal_ids):
        """
        Return list to generate rows of the CSV file
        """
        self.ensure_one()
        self.env.cr.execute("""  select aac.code as analytic_code,
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
                        AND account_move_line.date >= %(date_start)s
                        AND account_move_line.date <= %(date_end)s
                        group by aac.id,aac.code,aac.name,ac.id,ac.code,ac.name
                        order by aac.code
                   """, {'date_start': self.date_start,
                         'date_end': self.date_end})
        res = self.env.cr.fetchall()

        rows = []
        for line in res:
            rows.append(list(line))
        return rows

    def action_manual_export_journal_entries(self):
        """
        Here we use TemporaryFile to avoid full filling the Odoo worker
        Memory
        We also write the data to the wizard with SQL query as write seems
        to use too much memory as well.

        Those improvements permitted to improve the export from a 100k line to
        200k lines
        with default `limit_memory_hard = 805306368` (768MB) with more lines,
        you might encounter a MemoryError when trying to download the file even
        if it has been generated.

        To be able to export bigger volume of data, it is advised to set
        limit_memory_hard to 2097152000 (2 GB) to generate the file and let
        Odoo load it in the wizard when trying to download it.

        Tested with up to a generation of 700k entry lines
        """
        self.ensure_one()
        rows = self._get_data("journal_entries")
        with tempfile.TemporaryFile() as file_data:
            writer = AccountingWriter(file_data)
            writer.writerows(rows)
            with tempfile.TemporaryFile() as base64_data:
                file_data.seek(0)
                base64.encode(file_data, base64_data)
                base64_data.seek(0)
                self.env.cr.execute("""
                UPDATE account_csv_export
                SET data = %s
                WHERE id = %s""", (base64_data.read(), self.id))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.csv.export',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _get_header_journal_entries(self):
        return [
            # Standard Sage export fields
            _('DATE'),
            _('JOURNAL CODE'),
            _('ACCOUNT CODE'),
            _('PARTNER NAME'),
            _('REF'),
            _('DESCRIPTION'),
            _('DEBIT'),
            _('CREDIT'),
            _('FULL RECONCILE'),
            _('ANALYTIC ACCOUNT CODE'),

            # Other fields
            _('ENTRY NUMBER'),
            _('ACCOUNT NAME'),
            _('BALANCE'),
            _('AMOUNT CURRENCY'),
            _('CURRENCY'),
            _('ANALYTIC ACCOUNT NAME'),
            _('JOURNAL'),
            _('TAX CODE'),
            _('TAX NAME'),
            _('BANK STATEMENT'),
        ]

    def _get_rows_journal_entries(self, journal_ids):
        """
        Create a generator of rows of the CSV file
        """
        self.ensure_one()
        self.env.cr.execute("""
        SELECT
          account_move_line.date AS date,
          account_journal.name as journal,
          account_account.code AS account_code,
          res_partner.name AS partner_name,
          account_move_line.ref AS ref,
          account_move_line.name AS description,
          account_move_line.debit AS debit,
          account_move_line.credit AS credit,
          account_full_reconcile.name as full_reconcile,
          account_analytic_account.code AS analytic_account_code,
          account_move.name AS entry_number,
          account_account.name AS account_name,
          account_move_line.debit - account_move_line.credit AS balance,
          account_move_line.amount_currency AS amount_currency,
          res_currency.name AS currency,
          account_analytic_account.name AS analytic_account_name,
          account_journal.name as journal,
          acct.description as tax_code,
          acct.name as tax_name,
          account_bank_statement.name AS bank_statement
        FROM
          public.account_move_line
          JOIN account_account on
            (account_account.id=account_move_line.account_id)
          JOIN account_journal on
            (account_journal.id = account_move_line.journal_id)
          LEFT JOIN res_currency on
            (res_currency.id=account_move_line.currency_id)
          LEFT JOIN account_full_reconcile on
            (account_full_reconcile.id = account_move_line.full_reconcile_id)
          LEFT JOIN res_partner on
            (res_partner.id=account_move_line.partner_id)
          LEFT JOIN account_move on
            (account_move.id=account_move_line.move_id)
          LEFT JOIN account_analytic_account on
            (account_analytic_account.id=account_move_line.analytic_account_id)
          LEFT JOIN account_bank_statement on
            (account_bank_statement.id=account_move_line.statement_id)
          LEFT JOIN account_tax acct on
            (acct.id=account_move_line.tax_line_id)
        WHERE account_move_line.date >= %(date_start)s
        AND account_move_line.date <= %(date_end)s
        AND account_journal.id IN %(journal_ids)s
        ORDER BY account_move_line.date
        """, {'journal_ids': tuple(journal_ids),
              'date_start': self.date_start,
              'date_end': self.date_end})
        while 1:
            # http://initd.org/psycopg/docs/cursor.html#cursor.fetchmany
            # Set cursor.arraysize to minimize network round trips
            self.env.cr.arraysize = 100
            rows = self.env.cr.fetchmany()
            if not rows:
                break
            for row in rows:
                yield row

    def _get_data(self, result_type):
        self.ensure_one()
        get_header_func = getattr(
            self, ("_get_header_%s" % (result_type)), None)
        get_rows_func = getattr(self, ("_get_rows_%s" % (result_type)), None)
        if self.journal_ids:
            journal_ids = [x.id for x in self.journal_ids]
        else:
            j_obj = self.env["account.journal"]
            journal_ids = j_obj.search([]).ids
        rows = itertools.chain((get_header_func(),),
                               get_rows_func(journal_ids))
        return rows
