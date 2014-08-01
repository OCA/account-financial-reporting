#==============================================================================
#                                                                             =
#    mis_builder module for OpenERP, Management Information System Builder
#    Copyright (C) 2014 ACSONE SA/NV (<http://acsone.eu>)
#                                                                             =
#    This file is a part of mis_builder
#                                                                             =
#    mis_builder is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#                                                                             =
#    mis_builder is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#                                                                             =
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#                                                                             =
#==============================================================================

import xlwt
from datetime import datetime
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.tools.translate import translate
import logging
_logger = logging.getLogger(__name__)

_ir_translation_name = 'mis.report.instance.xls'


class mis_builder_xls_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(mis_builder_xls_parser, self).__init__(cr, uid, name, context=context)
        self.context = context
        self.localcontext.update({
            'datetime': datetime,
            '_': self._,
        })

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(self.cr, _ir_translation_name, 'report', lang, src) or src


class mis_builder_xls(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True, store=False):
        super(mis_builder_xls, self).__init__(name, table, rml, parser, header, store)

        # Cell Styles
        _xs = self.xls_styles
        # header
        rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rh_cell_style = xlwt.easyxf(rh_cell_format)
        self.rh_cell_style_center = xlwt.easyxf(rh_cell_format + _xs['center'])
        self.rh_cell_style_right = xlwt.easyxf(rh_cell_format + _xs['right'])
        # lines
        mis_cell_format = _xs['borders_all']
        self.mis_cell_style = xlwt.easyxf(mis_cell_format)
        self.mis_cell_style_center = xlwt.easyxf(mis_cell_format + _xs['center'])
        self.mis_cell_style_date = xlwt.easyxf(mis_cell_format + _xs['left'], num_format_str=report_xls.date_format)
        self.mis_cell_style_decimal = xlwt.easyxf(mis_cell_format + _xs['right'], num_format_str=report_xls.decimal_format)

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        _ = _p._

        report_name = objects[0].name
        ws = wb.add_sheet(report_name[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
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

        # get the computed result
        data = self.pool.get('mis.report.instance').compute(self.cr, self.uid, objects[0].id)

        # Column headers
        header_name_list = ['']
        col_specs_template = {'': {'header': [1, 42, 'text', ''],
                                   'header_date': [1, 42, 'text', '']}}
        for col in data['header']['']['cols']:
            col_specs_template[col['name']] = {'header': [1, 42, 'text', col['name']],
                                               'header_date': [1, 42, 'text', col['date']]}
            header_name_list.append(col['name'])
        c_specs = map(lambda x: self.render(x, col_specs_template, 'header', render_space={'_': _p._}), header_name_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.rh_cell_style, set_column_size=True)
        ws.set_horz_split_pos(row_pos)
        c_specs = map(lambda x: self.render(x, col_specs_template, 'header_date', render_space={'_': _p._}), header_name_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.rh_cell_style, set_column_size=True)
        ws.set_horz_split_pos(row_pos)

        for key in data['content']:
            line = data['content'][key]
            kpi_list = [line['kpi_name']]
            col_specs_template = {line['kpi_name']: {'lines': [1, 42, 'text', line['kpi_name']]}}
            col_count = 0
            for value in line['cols']:
                col_count = col_count + 1
                kpi_value_name = '_'.join([line['kpi_name'], str(col_count)])
                kpi_list.append(kpi_value_name)
                if value.get('val'):
                    col_specs_template[kpi_value_name] = {'lines': [1, 42, 'number', value['val']]}
                else:
                    col_specs_template[kpi_value_name] = {'lines': [1, 42, 'text', value['val_r']]}

            c_specs = map(lambda x: self.render(x, col_specs_template, 'lines'), kpi_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.mis_cell_style)

mis_builder_xls('report.mis.report.instance.xls',
    'mis.report.instance',
    parser=mis_builder_xls_parser)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
