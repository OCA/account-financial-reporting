# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import xlwt
from datetime import datetime
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell, _render
from .nov_account_journal import NovJournalPrint
from openerp.tools.translate import _
from openerp.exceptions import except_orm
import logging
_logger = logging.getLogger(__name__)


class AccountJournalXlsParser(NovJournalPrint):

    # pylint: disable=old-api7-method-defined
    def __init__(self, cr, uid, name, context):
        super(AccountJournalXlsParser, self).__init__(
            cr, uid, name, context=context)
        journal_obj = self.pool.get('account.journal')
        self.context = context
        wanted_list = journal_obj._report_xls_fields(cr, uid, context)
        template_changes = journal_obj._report_xls_template(cr, uid, context)
        self.localcontext.update({
            'datetime': datetime,
            'wanted_list': wanted_list,
            'template_changes': template_changes,
        })


class AccountJournalXls(report_xls):

    # pylint: disable=old-api7-method-defined
    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(AccountJournalXls, self).__init__(
            name, table, rml, parser, header, store)

        # Cell Styles
        _xs = self.xls_styles
        # header
        rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rh_cell_style = xlwt.easyxf(rh_cell_format)
        self.rh_cell_style_center = xlwt.easyxf(rh_cell_format + _xs['center'])
        self.rh_cell_style_right = xlwt.easyxf(rh_cell_format + _xs['right'])
        # lines
        aml_cell_format = _xs['borders_all']
        self.aml_cell_style = xlwt.easyxf(aml_cell_format)
        self.aml_cell_style_center = xlwt.easyxf(
            aml_cell_format + _xs['center'])
        self.aml_cell_style_date = xlwt.easyxf(
            aml_cell_format + _xs['left'],
            num_format_str=report_xls.date_format)
        self.aml_cell_style_decimal = xlwt.easyxf(
            aml_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)
        # totals
        rt_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rt_cell_style = xlwt.easyxf(rt_cell_format)
        self.rt_cell_style_right = xlwt.easyxf(rt_cell_format + _xs['right'])
        self.rt_cell_style_decimal = xlwt.easyxf(
            rt_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        # XLS Template Journal Items
        self.col_specs_lines_template = {
            'move_name': {
                'header': [1, 20, 'text', _render("_('Entry')")],
                'lines':
                [1, 0, 'text',
                 _render("l['move_name'] != '/' and l['move_name'] \
                 or ('*'+str(l['move_id']))")],
                'totals': [1, 0, 'text', None]},
            'move_date': {
                'header': [1, 13, 'text', _render("_('Date')")],
                'lines':
                [1, 0, 'date',
                 _render("datetime.strptime(l['move_date'],'%Y-%m-%d')"),
                 None, self.aml_cell_style_date],
                'totals': [1, 0, 'text', None]},
            'acc_code': {
                'header': [1, 12, 'text',  _render("_('Account')")],
                'lines': [1, 0, 'text', _render("l['acc_code']")],
                'totals': [1, 0, 'text', None]},
            'acc_name': {
                'header': [1, 36, 'text', _render("_('Account Name')")],
                'lines': [1, 0, 'text', _render("l['acc_name']")],
                'totals': [1, 0, 'text', None]},
            'aml_name': {
                'header': [1, 42, 'text', _render("_('Description')")],
                'lines': [1, 0, 'text', _render("l['aml_name']")],
                'totals': [1, 0, 'text', None]},
            'period': {
                'header': [1, 12, 'text', _render("_('Period')")],
                'lines': [1, 0, 'text', _render("l['period']")],
                'totals': [1, 0, 'text', None]},
            'journal': {
                'header': [1, 20, 'text', _render("_('Journal')")],
                'lines': [1, 0, 'text', _render("l['journal']")],
                'totals': [1, 0, 'text', None]},
            'journal_code': {
                'header': [1, 10, 'text', _render("_('Journal')")],
                'lines': [1, 0, 'text', _render("l['journal_code']")],
                'totals': [1, 0, 'text', None]},
            'analytic_account': {
                'header': [1, 20, 'text', _render("_('Analytic Account')")],
                'lines': [1, 0, 'text', _render("l['an_acc_name']")],
                'totals': [1, 0, 'text', None]},
            'analytic_account_code': {
                'header': [1, 20, 'text', _render("_('Analytic Account')")],
                'lines': [1, 0, 'text', _render("l['an_acc_code']")],
                'totals': [1, 0, 'text', None]},
            'partner_name': {
                'header': [1, 36, 'text', _render("_('Partner')")],
                'lines': [1, 0, 'text', _render("l['partner_name']")],
                'totals': [1, 0, 'text', None]},
            'partner_ref': {
                'header': [1, 36, 'text', _render("_('Partner Reference')")],
                'lines': [1, 0, 'text', _render("l['partner_ref']")],
                'totals': [1, 0, 'text', None]},
            'date_maturity': {
                'header': [1, 13, 'text', _render("_('Maturity Date')")],
                'lines':
                [1, 0,
                 _render("l['date_maturity'] and 'date' or 'text'"),
                 _render(
                     "l['date_maturity'] and datetime.\
                     strptime(l['date_maturity'],'%Y-%m-%d') or None"),
                    None, self.aml_cell_style_date],
                'totals': [1, 0, 'text', None]},
            'debit': {
                'header': [1, 18, 'text', _render("_('Debit')"), None,
                           self.rh_cell_style_right],
                'lines': [1, 0, 'number', _render("l['debit']"), None,
                          self.aml_cell_style_decimal],
                'totals': [1, 0, 'number', None, _render("debit_formula"),
                           self.rt_cell_style_decimal]},
            'credit': {
                'header': [1, 18, 'text', _render("_('Credit')"), None,
                           self.rh_cell_style_right],
                'lines': [1, 0, 'number', _render("l['credit']"), None,
                          self.aml_cell_style_decimal],
                'totals': [1, 0, 'number', None, _render("credit_formula"),
                           self.rt_cell_style_decimal]},
            'balance': {
                'header': [1, 18, 'text', _render("_('Balance')"), None,
                           self.rh_cell_style_right],
                'lines': [1, 0, 'number', None, _render("bal_formula"),
                          self.aml_cell_style_decimal],
                'totals': [1, 0, 'number', None, _render("bal_formula"),
                           self.rt_cell_style_decimal]},
            'reconcile': {
                'header': [1, 12, 'text', _render("_('Rec.')"), None,
                           self.rh_cell_style_center],
                'lines': [1, 0, 'text', _render("l['reconcile']"), None,
                          self.aml_cell_style_center],
                'totals': [1, 0, 'text', None]},
            'reconcile_partial': {
                'header': [1, 12, 'text', _render("_('Part. Rec.')"), None,
                           self.rh_cell_style_center],
                'lines': [1, 0, 'text', _render("l['reconcile_partial']"),
                          None, self.aml_cell_style_center],
                'totals': [1, 0, 'text', None]},
            'tax_code': {
                'header': [1, 6, 'text', _render("_('VAT')"), None,
                           self.rh_cell_style_center],
                'lines': [1, 0, 'text', _render("l['tax_code']"), None,
                          self.aml_cell_style_center],
                'totals': [1, 0, 'text', None]},
            'tax_amount': {
                'header': [1, 18, 'text', _render("_('VAT Amount')"), None,
                           self.rh_cell_style_right],
                'lines': [1, 0, 'number', _render("l['tax_amount']"), None,
                          self.aml_cell_style_decimal],
                'totals': [1, 0, 'text', None]},
            'amount_currency': {
                'header': [1, 18, 'text', _render("_('Am. Currency')"), None,
                           self.rh_cell_style_right],
                'lines':
                [1, 0,
                 _render("l['amount_currency'] and 'number' or 'text'"),
                 _render("l['amount_currency'] or None"),
                 None, self.aml_cell_style_decimal],
                'totals': [1, 0, 'text', None]},
            'currency_name': {
                'header': [1, 6, 'text', _render("_('Curr.')"), None,
                           self.rh_cell_style_center],
                'lines': [1, 0, 'text', _render("l['currency_name']"), None,
                          self.aml_cell_style_center],
                'totals': [1, 0, 'text', None]},
            'docname': {
                'header': [1, 35, 'text', _render("_('Document')")],
                'lines': [1, 0, 'text', _render("l['docname']")],
                'totals': [1, 0, 'text', None]},
            'move_ref': {
                'header': [1, 25, 'text', _render("_('Entry Reference')")],
                'lines': [1, 0, 'text', _render("l['move_ref']")],
                'totals': [1, 0, 'text', None]},
            'move_id': {
                'header': [1, 10, 'text', _render("_('Entry Id')")],
                'lines': [1, 0, 'text', _render("str(l['move_id'])")],
                'totals': [1, 0, 'text', None]},
        }

        # XLS Template VAT Summary
        self.col_specs_vat_summary_template = {
            'tax_case_name': {
                'header': [1, 45, 'text', _render("_('Description')")],
                'tax_totals': [1, 0, 'text', _render("t.name")]},
            'tax_code': {
                'header': [1, 6, 'text', _render("_('Case')")],
                'tax_totals': [1, 0, 'text', _render("t.code")]},
            'tax_amount': {
                'header': [1, 18, 'text', _render("_('Amount')"), None,
                           self.rh_cell_style_right],
                'tax_totals': [1, 0, 'number', _render("sum_vat(o,t)"), None,
                               self.aml_cell_style_decimal]},
        }

    def _journal_title(self, o, ws, _p, row_pos, _xs):
        cell_style = xlwt.easyxf(_xs['xls_title'])
        report_name = (10 * ' ').join([
            _p.company.name,
            _p.title(o)[0],
            _p.title(o)[1],
            _p._("Journal Overview") + ' - ' + _p.company.currency_id.name,
        ])
        c_specs = [
            ('report_name', 1, 0, 'text', report_name),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style)
        return row_pos + 1

    def _journal_lines(self, o, ws, _p, row_pos, _xs):

        wanted_list = self.wanted_list
        debit_pos = self.debit_pos
        credit_pos = self.credit_pos

        # Column headers
        c_specs = map(lambda x: self.render(
            x, self.col_specs_lines_template, 'header',
            render_space={'_': _p._}), wanted_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=self.rh_cell_style,
            set_column_size=True)
        ws.set_horz_split_pos(row_pos)

        # account move lines
        aml_start_pos = row_pos
        aml_cnt = len(_p.lines(o))
        cnt = 0
        for l in _p.lines(o):
            cnt += 1
            debit_cell = rowcol_to_cell(row_pos, debit_pos)
            credit_cell = rowcol_to_cell(row_pos, credit_pos)
            bal_formula = debit_cell + '-' + credit_cell
            _logger.debug('dummy call - %s', bal_formula)
            c_specs = map(
                lambda x: self.render(x, self.col_specs_lines_template,
                                      'lines'), wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, row_style=self.aml_cell_style)
            if l['draw_line'] and cnt != aml_cnt:
                row_pos += 1

        # Totals
        debit_start = rowcol_to_cell(aml_start_pos, debit_pos)
        debit_stop = rowcol_to_cell(row_pos - 1, debit_pos)
        debit_formula = 'SUM(%s:%s)' % (debit_start, debit_stop)
        _logger.debug('dummy call - %s', debit_formula)
        credit_start = rowcol_to_cell(aml_start_pos, credit_pos)
        credit_stop = rowcol_to_cell(row_pos - 1, credit_pos)
        credit_formula = 'SUM(%s:%s)' % (credit_start, credit_stop)
        _logger.debug('dummy call - %s', credit_formula)
        debit_cell = rowcol_to_cell(row_pos, debit_pos)
        credit_cell = rowcol_to_cell(row_pos, credit_pos)
        bal_formula = debit_cell + '-' + credit_cell
        c_specs = map(lambda x: self.render(
            x, self.col_specs_lines_template, 'totals'), wanted_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=self.rt_cell_style_right)
        return row_pos + 1

    def _journal_vat_summary(self, o, ws, _p, row_pos, _xs):

        if not _p.tax_codes(o):
            return row_pos

        title_cell_style = xlwt.easyxf(_xs['bold'])
        c_specs = [('summary_title', 1, 0, 'text', _p._("VAT Declaration"))]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=title_cell_style) + 1

        wanted_list = self.wanted_list
        vat_summary_wanted_list = ['tax_case_name', 'tax_code', 'tax_amount']

        # calculate col_span
        cols_number = len(wanted_list)
        vat_summary_cols_number = len(vat_summary_wanted_list)
        if vat_summary_cols_number > cols_number:
            raise except_orm(
                _('Programming Error!'),
                _("vat_summary_cols_number should be < cols_number !"))
        index = 0
        for i in range(vat_summary_cols_number):
            col = vat_summary_wanted_list[i]
            col_size = self.col_specs_lines_template[
                wanted_list[index]]['header'][1]
            templ_col_size = self.col_specs_vat_summary_template[
                col]['header'][1]
            # _logger.warn("col=%s, col_size=%s, templ_col_size=%s",
            # col, col_size, templ_col_size)
            col_span = 1
            if templ_col_size > col_size:
                new_size = col_size
                while templ_col_size > new_size:
                    col_span += 1
                    index += 1
                    new_size += self.col_specs_lines_template[
                        wanted_list[index]]['header'][1]
            self.col_specs_vat_summary_template[col]['header'][0] = col_span
            self.col_specs_vat_summary_template[
                col]['tax_totals'][0] = col_span
            index += 1

        c_specs = map(lambda x: self.render(
            x, self.col_specs_vat_summary_template, 'header'),
            vat_summary_wanted_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=self.rh_cell_style)

        for t in _p.tax_codes(o):
            c_specs = map(lambda x: self.render(
                x, self.col_specs_vat_summary_template, 'tax_totals'),
                vat_summary_wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, row_style=self.aml_cell_style)

        return row_pos

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        wanted_list = _p.wanted_list
        if _p.display_currency:
            wanted_list += ['amount_currency', 'currency_name']
        self.wanted_list = wanted_list
        self.col_specs_lines_template.update(_p.template_changes)

        self.debit_pos = 'debit' in wanted_list and wanted_list.index('debit')
        self.credit_pos = 'credit' in wanted_list and wanted_list.index(
            'credit')
        if not (self.credit_pos and self.debit_pos) and 'balance' \
                in wanted_list:
            raise except_orm(
                _('Customisation Error!'),
                _("The 'Balance' field is a calculated XLS \
                  field requiring the presence of the \
                  'Debit' and 'Credit' fields !")
            )

        for o in objects:

            sheet_name = ' - '.join([o[1].code, o[0].code]
                                    )[:31].replace('/', '-')
            sheet_name = sheet_name[:31].replace('/', '-')
            ws = wb.add_sheet(sheet_name)
            ws.panes_frozen = True
            ws.remove_splits = True
            ws.portrait = 0  # Landscape
            ws.fit_width_to_pages = 1
            row_pos = 0

            # set print header/footer
            ws.header_str = self.xls_headers['standard']
            ws.footer_str = self.xls_footers['standard']

            # Data
            row_pos = self._journal_title(o, ws, _p, row_pos, _xs)
            row_pos = self._journal_lines(o, ws, _p, row_pos, _xs)
            row_pos = self._journal_vat_summary(o, ws, _p, row_pos, _xs)


AccountJournalXls(
    'report.nov.account.journal.xls', 'account.journal.period',
    parser=AccountJournalXlsParser,
)
