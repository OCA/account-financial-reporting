# -*- coding: utf-8 -*-
# © 2017 Akretion France (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from odoo import fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime


class BankReconciliationXlsx(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, wizard):
        date = wizard.date
        date_dt = fields.Date.from_string(date)
        no_bank_journal = True
        for o in wizard.journal_ids:
            no_bank_journal = False
            # Start styles
            lang_code = self.env.user.lang
            lang = False
            if lang_code:
                lang = self.env['res.lang'].search([('code', '=', lang_code)])
            if not lang:
                lang = self.env['res.lang'].search([], limit=1)
            xls_date_format = lang.date_format.replace('%Y', 'yyyy').\
                replace('%m', 'mm').replace('%d', 'dd').replace('%y', 'yy')

            doc_title = workbook.add_format({'bold': True, 'font_size': 16})
            col_title = workbook.add_format({
                'bold': True, 'bg_color': '#e2e2fa',
                'text_wrap': True, 'font_size': 10,
                })
            title_right = workbook.add_format({
                'bold': True, 'bg_color': '#e6e6fa',
                'font_size': 10, 'align': 'right',
                })
            title_date = workbook.add_format({
                'bg_color': '#f6f6ff', 'bold': True,
                'num_format': xls_date_format,
                'font_size': 10,
                'align': 'left'})
            label_bold = workbook.add_format({
                'bold': True, 'text_wrap': False, 'font_size': 10})
            none = workbook.add_format({
                'bold': True, 'font_size': 10, 'align': 'right'})
            regular = workbook.add_format({'font_size': 10})
            if '%' in xls_date_format:
                # fallback
                xls_date_format = 'yyyy-mm-dd'
            regular_date = workbook.add_format({
                'num_format': xls_date_format,
                'font_size': 10,
                'align': 'left'})
            cur_format = u'#,##0.00 %s' % (
                o.company_id.currency_id.symbol or
                o.company_id.currency_id.name)
            # It seems that Excel replaces automatically the decimal
            # and thousand separator by those of the language under which
            # Excel runs
            regular_currency = workbook.add_format(
                {'num_format': cur_format, 'font_size': 10})
            regular_currency_bg = workbook.add_format({
                'num_format': cur_format, 'font_size': 10,
                'bg_color': '#f6f6ff'})
            # End styles

            sheet = workbook.add_worksheet(o.code or o.name)
            sheet.write(
                0, 0,
                _('%s - %s - Bank Reconciliation') % (
                    o.company_id.name, o.display_name),
                doc_title)
            sheet.set_row(0, 26)
            sheet.set_row(1, 25)
            sheet.set_column(0, 0, 10)
            sheet.set_column(1, 1, 40)
            sheet.set_column(2, 2, 15)
            sheet.set_column(3, 3, 25)
            sheet.set_column(4, 4, 12)
            sheet.set_column(5, 5, 18)
            sheet.set_column(6, 6, 14)
            sheet.set_column(7, 7, 14)
            row = 2
            sheet.write(row, 0, _("Date:"), title_right)
            sheet.write(row, 1, date_dt, title_date)
            # 1) Show accounting balance of bank account
            row += 2
            bank_account = o.default_debit_account_id
            for col in range(3):
                sheet.write(row, col, '', title_right)
            sheet.write(
                row, 3,
                _('Balance %s:') % bank_account.code, title_right)
            amount_field = 'balance'
            # TODO: add support for bank accounts in foreign currency
            # if not o.currency_id else 'amount_currency'
            query = """
                SELECT sum(%s) FROM account_move_line
                WHERE account_id=%%s AND date <= %%s""" % (amount_field, )
            self.env.cr.execute(query, (bank_account.id, date))
            query_results = self.env.cr.dictfetchall()
            if query_results:
                account_bal = query_results[0].get('sum') or 0.0
            else:
                account_bal = 0.0

            sheet.write(row, 4, account_bal, regular_currency_bg)
            bank_bal = account_bal
            formula = '=E%d' % (row + 1)
            # 2) Show account move line that are not linked to bank statement
            # line or linked to a statement line after the date
            row += 2
            sheet.write(
                row, 0, _(
                    'Journal items of account %s not linked to a bank '
                    'statement line:') % bank_account.code,
                label_bold)
            mlines = self.env['account.move.line'].search([
                ('account_id', '=', bank_account.id),
                ('journal_id', '=', o.id),  # to avoid initial line
                ('date', '<=', date),
                '|', ('statement_line_date', '=', False),
                ('statement_line_date', '>', date)])
            if not mlines:
                sheet.write(row, 4, _('NONE'), none)
            else:
                row += 1
                col_labels = [
                    _('Date'), _('Label'), _('Ref.'), _('Partner'),
                    _('Amount'), _('Statement Line Date'), _('Move Number'),
                    _('Counter-part')]
                col = 0
                for col_label in col_labels:
                    sheet.write(row, col, col_label, col_title)
                    col += 1
                m_start_row = m_end_row = row + 1
                for mline in mlines:
                    row += 1
                    m_end_row = row
                    move = mline.move_id
                    bank_bal -= mline.balance
                    date_dt = fields.Date.from_string(mline.date)
                    sheet.write(row, 0, date_dt, regular_date)
                    sheet.write(row, 1, mline.name, regular)
                    sheet.write(row, 2, mline.ref or '', regular)
                    sheet.write(
                        row, 3, mline.partner_id.display_name or '', regular)
                    sheet.write(row, 4, mline.balance, regular_currency)
                    if mline.statement_line_date:
                        stl_date_dt = fields.Date.from_string(
                            mline.statement_line_date)
                    else:
                        stl_date_dt = ''
                    sheet.write(row, 5, stl_date_dt, regular_date)
                    sheet.write(row, 6, move.name, regular)
                    # counter-part accounts
                    cpart = []
                    for line in move.line_ids:
                        if (
                                line.account_id != bank_account and
                                line.account_id.code not in cpart):
                            cpart.append(line.account_id.code)
                    sheet.write(row, 7, ' ,'.join(cpart), regular)

                formula += '-SUM(E%d:E%d)' % (m_start_row + 1, m_end_row + 1)

            # 3) Add draft bank statement lines
            row += 2  # skip 1 line
            sheet.write(
                row, 0, _(
                    'Draft bank statement lines:'),
                label_bold)
            blines = self.env['account.bank.statement.line'].search([
                ('journal_entry_ids', '=', False),
                ('journal_id', '=', o.id),
                ('date', '<=', date)])
            if not blines:
                sheet.write(row, 4, _('NONE'), none)
            else:
                row += 1
                col_labels = [
                    _('Date'), _('Label'), _('Ref.'),
                    _('Partner'), _('Amount'), _('Statement Ref.'), '', '']
                col = 0
                for col_label in col_labels:
                    sheet.write(row, col, col_label, col_title)
                    col += 1
                b_start_row = b_end_row = row + 1
                for bline in blines:
                    row += 1
                    b_end_row = row
                    bank_bal += bline.amount
                    date_dt = datetime.strptime(
                        bline.date, DEFAULT_SERVER_DATE_FORMAT)
                    sheet.write(row, 0, date_dt, regular_date)
                    sheet.write(row, 1, bline.name, regular)
                    sheet.write(row, 2, bline.ref or '', regular)
                    sheet.write(
                        row, 3, bline.partner_id.display_name or '', regular)
                    sheet.write(row, 4, bline.amount, regular_currency)
                    sheet.write(
                        row, 5, bline.statement_id.display_name or '',
                        regular_currency)
                formula += '+SUM(E%d:E%d)' % (b_start_row + 1, b_end_row + 1)

            # 4) Theoric bank account balance at the bank
            row += 2
            for col in range(3):
                sheet.write(row, col, '', title_right)
            sheet.write(
                row, 3, _('Computed Bank Account Balance at the Bank:'),
                title_right)
            sheet.write_formula(
                row, 4, formula, regular_currency_bg, bank_bal)
        if no_bank_journal:
            sheet = workbook.add_worksheet(_('No Bank Journal'))
            sheet.set_row(0, 30)
            warn_msg = workbook.add_format(
                {'bold': True, 'font_size': 16, 'font_color': '#003b6f'})
            sheet.write(
                0, 0, _(
                    "No bank journal selected. "
                    "This report is only for bank journals."), warn_msg)


BankReconciliationXlsx(
    'report.bank.reconciliation.xlsx', 'bank.reconciliation.report.wizard')
