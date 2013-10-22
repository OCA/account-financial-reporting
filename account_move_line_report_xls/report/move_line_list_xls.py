# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.com). All rights reserved.
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

import xlwt
import time
from datetime import datetime
from report import report_sxw
from report_xls.report_xls import report_xls
from report_xls.utils import rowcol_to_cell, _render
from account_move_line_report.report.move_line_list_print import move_line_list_print
from tools.translate import _
import pooler
import logging
_logger = logging.getLogger(__name__)


class move_line_xls_parser(report_sxw.rml_parse):
           
    def __init__(self, cr, uid, name, context):
        super(move_line_xls_parser, self).__init__(cr, uid, name, context=context)
        self.context = context
        wanted_list = self.pool.get('account.move.line')._report_xls_fields(cr, uid, context)
        self.localcontext.update({
            'datetime': datetime,
            'wanted_list': wanted_list,
        })

class move_line_xls(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True, store=False):
        super(move_line_xls, self).__init__(name, table, rml, parser, header, store)

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
        self.aml_cell_style_center = xlwt.easyxf(aml_cell_format + _xs['center'])
        self.aml_cell_style_date = xlwt.easyxf(aml_cell_format + _xs['left'], num_format_str = report_xls.date_format)
        self.aml_cell_style_decimal = xlwt.easyxf(aml_cell_format + _xs['right'], num_format_str = report_xls.decimal_format)
        # totals
        rt_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rt_cell_style = xlwt.easyxf(rt_cell_format)
        self.rt_cell_style_right = xlwt.easyxf(rt_cell_format + _xs['right'])       
        self.rt_cell_style_decimal = xlwt.easyxf(rt_cell_format + _xs['right'], num_format_str = report_xls.decimal_format)
        
        # XLS Template
        self.col_specs_template = {
            'move':{
                'header': [1, 20, 'text', _('Move')],
                'lines': [1, 0, 'text', _render("line.move_id.name or ''")],
                'totals': [1, 0, 'text', None]},
            'name':{      
                'header': [1, 42, 'text', _('Name')],
                'lines': [1, 0, 'text', _render("line.name or ''")],                
                'totals': [1, 0, 'text', None]},
            'ref':{      
                'header': [1, 42, 'text', _('Reference')],
                'lines': [1, 0, 'text', _render("line.ref or ''")],                
                'totals': [1, 0, 'text', None]},
            'date':{      
                'header': [1, 13, 'text', _('Effective Date')],
                'lines': [1, 0, 'date', _render("datetime.strptime(line.date,'%Y-%m-%d')"), None, self.aml_cell_style_date],
                'totals': [1, 0, 'text', None]},
            'period':{      
                'header': [1, 12, 'text', _('Period')],
                'lines': [1, 0, 'text', _render("line.period_id.code or ''")],
                'totals': [1, 0, 'text', None]},
            'partner':{
                'header': [1, 36, 'text',  _('Partner')],
                'lines': [1, 0, 'text', _render("line.partner_id and line.partner_id.name or ''")],
                'totals': [1, 0, 'text', None]},
            'partner_ref':{
                'header': [1, 36, 'text',  _('Partner Reference')],
                'lines': [1, 0, 'text', _render("line.partner_id and line.partner_id.ref or ''")],
                'totals': [1, 0, 'text', None]},
            'account':{
                'header': [1, 12, 'text',  _('Account')],
                'lines': [1, 0, 'text', _render("line.account_id.code")],
                'totals': [1, 0, 'text', None]},
            'date_maturity':{
                'header': [1, 13, 'text',  _('Maturity Date')],
                'lines': [1, 0, _render("line.date_maturity.val and 'date' or 'text'"),
                    _render("line.date_maturity.val and datetime.strptime(line.date_maturity,'%Y-%m-%d') or None"),
                    None, self.aml_cell_style_date],
                'totals': [1, 0, 'text', None]},
            'debit':{
                'header': [1, 18, 'text',  _('Debit'), None, self.rh_cell_style_right],
                'lines': [1, 0, 'number', _render("line.debit"), None, self.aml_cell_style_decimal],
                'totals': [1, 0, 'number', None, _render("debit_formula"), self.rt_cell_style_decimal]},
            'credit':{
                'header': [1, 18, 'text',  _('Credit'), None, self.rh_cell_style_right],
                'lines': [1, 0, 'number', _render("line.credit"), None, self.aml_cell_style_decimal],
                'totals': [1, 0, 'number', None, _render("credit_formula"), self.rt_cell_style_decimal]},
            'balance':{
                'header': [1, 18, 'text',   _('Balance'), None, self.rh_cell_style_right],
                'lines': [1, 0, 'number', None, _render("bal_formula"), self.aml_cell_style_decimal],
                'totals': [1, 0, 'number', None, _render("bal_formula"), self.rt_cell_style_decimal]},
            'reconcile':{
                'header': [1, 12, 'text',  _('Rec.'), None, self.rh_cell_style_center],
                'lines': [1, 0, 'text', _render("line.reconcile_id.name or ''"), None, self.aml_cell_style_center],
                'totals': [1, 0, 'text', None]},
            'reconcile_partial':{
                'header': [1, 12, 'text',  _('Part. Rec.'), None, self.rh_cell_style_center],
                'lines': [1, 0, 'text', _render("line.reconcile_partial_id.name or ''"), None, self.aml_cell_style_center],
                'totals': [1, 0, 'text', None]},
            'tax_code':{
                'header': [1, 12, 'text',  _('Tax Code'), None, self.rh_cell_style_center],
                'lines': [1, 0, 'text', _render("line.tax_code_id.code or ''"), None, self.aml_cell_style_center],
                'totals': [1, 0, 'text', None]},
            'tax_amount':{
                'header': [1, 18, 'text',  _('Tax/Base Amount'), None, self.rh_cell_style_right],
                'lines': [1, 0, 'number', _render("line.tax_amount"), None, self.aml_cell_style_decimal],
                'totals': [1, 0, 'text', None]},
        }
    
    def generate_xls_report(self, _p, _xs, data, objects, wb):

        wanted_list = _p.wanted_list
        
        if 'balance' in wanted_list:
            try:
                debit_pos = wanted_list.index('debit')
                credit_pos = wanted_list.index('credit')
            except:
                raise osv.except_osv(_('Customisation Error!'), 
                    _("The 'Balance' field is a calculated XLS field requiring the presence of the 'Debit' and 'Credit' fields !"))

        report_name = objects[0]._description or objects[0]._name
        ws = wb.add_sheet(report_name[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0 # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0
        
        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        # Title
        cell_style = xlwt.easyxf(_xs['xls_title'])
        c_specs = [
            ('report_name', 1, 0, 'text', report_name),
        ]       
        row_data = self.xls_row_template(c_specs, ['report_name'])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style)
        row_pos += 1

        # Column headers
        c_specs = map(lambda x: self.render(x, self.col_specs_template, 'header', render_space={}), wanted_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.rh_cell_style, set_column_size=True)        
        ws.set_horz_split_pos(row_pos)   
        
        # account move lines
        for line in objects:
            debit_cell = rowcol_to_cell(row_pos, debit_pos)
            credit_cell = rowcol_to_cell(row_pos, credit_pos)
            bal_formula = debit_cell + '-' + credit_cell
            c_specs = map(lambda x: self.render(x, self.col_specs_template, 'lines'), wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.aml_cell_style)

        # Totals           
        aml_cnt = len(objects)
        debit_start = rowcol_to_cell(row_pos - aml_cnt, debit_pos)
        debit_stop = rowcol_to_cell(row_pos - 1, debit_pos)
        debit_formula = 'SUM(%s:%s)' %(debit_start, debit_stop)
        credit_start = rowcol_to_cell(row_pos - aml_cnt, credit_pos)
        credit_stop = rowcol_to_cell(row_pos - 1, credit_pos)
        credit_formula = 'SUM(%s:%s)' %(credit_start, credit_stop)
        debit_cell = rowcol_to_cell(row_pos, debit_pos)
        credit_cell = rowcol_to_cell(row_pos, credit_pos)
        bal_formula = debit_cell + '-' + credit_cell
        c_specs = map(lambda x: self.render(x, self.col_specs_template, 'totals'), wanted_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.rt_cell_style_right) 

move_line_xls('report.move.line.list.xls', 
    'account.move.line',
    parser=move_line_xls_parser)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: