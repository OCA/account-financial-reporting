# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.report_xlsx_helper.report.abstract_report_xlsx \
    import AbstractReportXlsx
from odoo.report import report_sxw
from odoo.tools.translate import translate

_logger = logging.getLogger(__name__)

IR_TRANSLATION_NAME = 'move.line.list.xls'


class MoveLineXlsx(AbstractReportXlsx):

    def _(self, src):
        lang = self.env.context.get('lang', 'en_US')
        val = translate(
            self.env.cr, IR_TRANSLATION_NAME, 'report', lang, src) or src
        return val

    def _get_ws_params(self, workbook, data, amls):

        # XLSX Template
        col_specs = {
            'move': {
                'header': {
                    'value': self._('Entry'),
                },
                'lines': {
                    'value': self._render("line.move_id.name"),
                },
                'width': 20,
            },
            'name': {
                'header': {
                    'value': self._('Name'),
                },
                'lines': {
                    'value': self._render("line.name"),
                },
                'width': 42,
            },
            'ref': {
                'header': {
                    'value': self._('Reference'),
                },
                'lines': {
                    'value': self._render("line.ref"),
                },
                'width': 42,
            },
            'date': {
                'header': {
                    'value': self._('Effective Date'),
                },
                'lines': {
                    'value': self._render(
                        "datetime.strptime(line.date, '%Y-%m-%d')"),
                    'format': self.format_tcell_date_left,
                },
                'width': 13,
            },
            'partner': {
                'header': {
                    'value': self._('Partner'),
                },
                'lines': {
                    'value': self._render(
                        "line.partner_id and line.partner_id.name"),
                },
                'width': 36,
            },
            'partner_ref': {
                'header': {
                    'value': self._('Partner Reference'),
                },
                'lines': {
                    'value': self._render(
                        "line.partner_id and line.partner_id.ref"),
                },
                'width': 36,
            },
            'account': {
                'header': {
                    'value': self._('Account'),
                },
                'lines': {
                    'value': self._render(
                        "line.account_id.code"),
                },
                'width': 12,
            },
            'date_maturity': {
                'header': {
                    'value': self._('Maturity Date'),
                },
                'lines': {
                    'value': self._render(
                        "datetime.strptime(line.date_maturity,'%Y-%m-%d')"),
                    'format': self.format_tcell_date_left,
                },
                'width': 13,
            },
            'debit': {
                'header': {
                    'value': self._('Debit'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("line.debit"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render("debit_formula"),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'credit': {
                'header': {
                    'value': self._('Credit'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("line.credit"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render("credit_formula"),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'balance': {
                'header': {
                    'value': self._('Balance'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("line.balance"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render("bal_formula"),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'full_reconcile': {
                'header': {
                    'value': self._('Rec.'),
                    'format': self.format_theader_yellow_center,
                },
                'lines': {
                    'value': self._render(
                        "line.full_reconcile_id "
                        "and line.full_reconcile_id.name"),
                    'format': self.format_tcell_center,
                },
                'width': 12,
            },
            'reconcile_amount': {
                'header': {
                    'value': self._('Reconcile Amount'),
                },
                'lines': {
                    'value': self._render(
                        "line.full_reconcile_id and line.balance or "
                        "(sum(line.matched_credit_ids.mapped('amount')) - "
                        "sum(line.matched_debit_ids.mapped('amount')))"),
                    'format': self.format_tcell_amount_right,
                },
                'width': 12,
            },
            'matched_debit_ids': {
                'header': {
                    'value': self._('Matched Debits'),
                },
                'lines': {
                    'value': self._render(
                        "line.matched_debit_ids "
                        "and str([x.debit_move_id.id "
                        "for x in line.matched_debit_ids])"),
                },
                'width': 20,
            },
            'matched_credit_ids': {
                'header': {
                    'value': self._('Matched Credits'),
                },
                'lines': {
                    'value': self._render(
                        "line.matched_credit_ids "
                        "and str([x.credit_move_id.id "
                        "for x in line.matched_credit_ids])"),
                },
                'width': 20,
            },
            'amount_currency': {
                'header': {
                    'value': self._('Am. Currency'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("line.amount_currency"),
                    'format': self.format_tcell_amount_right,
                },
                'width': 18,
            },
            'currency_name': {
                'header': {
                    'value': self._('Curr.'),
                    'format': self.format_theader_yellow_center,
                },
                'lines': {
                    'value': self._render(
                        "line.currency_id and line.currency_id.name"),
                    'format': self.format_tcell_center,
                },
                'width': 6,
            },
            'journal': {
                'header': {
                    'value': self._('Journal'),
                },
                'lines': {
                    'value': self._render("line.journal_id.code"),
                },
                'width': 12,
            },
            'company_currency': {
                'header': {
                    'value': self._('Comp. Curr.'),
                    'format': self.format_theader_yellow_center,
                },
                'lines': {
                    'value': self._render(
                        "line.company_id.currency_id.name"),
                    'format': self.format_tcell_center,
                },
                'width': 10,
            },
            'analytic_account': {
                'header': {
                    'value': self._('Analytic Account Reference'),
                },
                'lines': {
                    'value': self._render(
                        "line.analytic_account_id "
                        "and line.analytic_account_id.code"),
                },
                'width': 36,
            },
            'analytic_account_name': {
                'header': {
                    'value': self._('Analytic Account'),
                },
                'lines': {
                    'value': self._render(
                        "line.analytic_account_id "
                        "and line.analytic_account_id.name"),
                },
                'width': 36,
            },
            'product': {
                'header': {
                    'value': self._('Product'),
                },
                'lines': {
                    'value': self._render(
                        "line.product_id and line.product_id.name"),
                },
                'width': 36,
            },
            'product_ref': {
                'header': {
                    'value': self._('Product Reference'),
                },
                'lines': {
                    'value': self._render(
                        "line.product_id and line.product_id.default_code "
                        "or ''"),
                },
                'width': 36,
            },
            'product_uom': {
                'header': {
                    'value': self._('Unit of Measure'),
                },
                'lines': {
                    'value': self._render(
                        "line.product_uom_id and line.product_uom_id.name"),
                },
                'width': 20,
            },
            'quantity': {
                'header': {
                    'value': self._('Qty'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("line.quantity"),
                    'format': self.format_tcell_amount_right,
                },
                'width': 8,
            },
            'statement': {
                'header': {
                    'value': self._('Statement'),
                },
                'lines': {
                    'value': self._render(
                        "line.statement_id and line.statement_id.name"),
                },
                'width': 20,
            },
            'invoice': {
                'header': {
                    'value': self._('Invoice'),
                },
                'lines': {
                    'value': self._render(
                        "line.invoice_id and line.invoice_id.number"),
                },
                'width': 20,
            },
            'amount_residual': {
                'header': {
                    'value': self._('Residual Amount'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("line.amount_residual"),
                    'format': self.format_tcell_amount_right,
                },
                'width': 18,
            },
            'amount_residual_currency': {
                'header': {
                    'value': self._('Res. Am. in Curr.'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("line.amount_residual_currency"),
                    'format': self.format_tcell_amount_right,
                },
                'width': 18,
            },
            'narration': {
                'header': {
                    'value': self._('Notes'),
                },
                'lines': {
                    'value': self._render("line.move_id.narration or ''"),
                },
                'width': 42,
            },
            'blocked': {
                'header': {
                    'value': self._('Lit.'),
                    'format': self.format_theader_yellow_center,
                },
                'lines': {
                    'value': self._render("line.blocked and 'x' or ''"),
                    'format': self.format_tcell_center,
                },
                'width': 4,
            },
            'id': {
                'header': {
                    'value': self._('Id'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("line.id"),
                    'format': self.format_tcell_integer_right,
                },
                'width': 12,
            },
        }
        col_specs.update(self.env['account.move.line']._report_xlsx_template())
        wanted_list = self.env['account.move.line']._report_xlsx_fields()
        title = self._("Journal Items")

        return [{
            'ws_name': title,
            'generate_ws_method': '_amls_export',
            'title': title,
            'wanted_list': wanted_list,
            'col_specs': col_specs,
        }]

    def _amls_export(self, workbook, ws, ws_params, data, amls):

        ws.set_landscape()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_ws_title(ws, row_pos, ws_params)

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='header',
            default_format=self.format_theader_yellow_left)

        ws.freeze_panes(row_pos, 0)

        wanted_list = ws_params['wanted_list']
        debit_pos = 'debit' in wanted_list and wanted_list.index('debit')
        credit_pos = 'credit' in wanted_list and wanted_list.index('credit')

        for line in amls:
            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='lines',
                render_space={'line': line},
                default_format=self.format_tcell_left)

        aml_cnt = len(amls)
        debit_start = self._rowcol_to_cell(row_pos - aml_cnt, debit_pos)
        debit_stop = self._rowcol_to_cell(row_pos - 1, debit_pos)
        debit_formula = 'SUM(%s:%s)' % (debit_start, debit_stop)
        credit_start = self._rowcol_to_cell(row_pos - aml_cnt, credit_pos)
        credit_stop = self._rowcol_to_cell(row_pos - 1, credit_pos)
        credit_formula = 'SUM(%s:%s)' % (credit_start, credit_stop)
        debit_cell = self._rowcol_to_cell(row_pos, debit_pos)
        credit_cell = self._rowcol_to_cell(row_pos, credit_pos)
        bal_formula = debit_cell + '-' + credit_cell
        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='totals',
            render_space={
                'debit_formula': debit_formula,
                'credit_formula': credit_formula,
                'bal_formula': bal_formula,
            },
            default_format=self.format_theader_yellow_left)


MoveLineXlsx('report.move.line.list.xls',
             'account.move.line',
             parser=report_sxw.rml_parse)
