# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import xlwt
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
import logging
_logger = logging.getLogger(__name__)


class MisBuilderXlsParser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(MisBuilderXlsParser, self).__init__(
            cr, uid, name, context=context)
        self.context = context


class MisBuilderXls(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(MisBuilderXls, self).__init__(
            name, table, rml, parser, header, store)

        # Cell Styles
        _xs = self.xls_styles
        # header
        rh_cell_format = _xs['bold'] + _xs['fill'] + \
            _xs['borders_all'] + _xs['right']
        self.rh_cell_style = xlwt.easyxf(rh_cell_format)
        self.rh_cell_style_date = xlwt.easyxf(
            rh_cell_format, num_format_str=report_xls.date_format)
        # lines
        self.mis_rh_cell_style = xlwt.easyxf(
            _xs['borders_all'] + _xs['bold'] + _xs['fill'])

    def generate_xls_report(self, _p, _xs, data, objects, wb):

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
        c_specs = [
            ('report_name', 1, 0, 'text', report_name),
        ]
        row_data = self.xls_row_template(c_specs, ['report_name'])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=xlwt.easyxf(_xs['xls_title']))
        row_pos += 1

        # get the computed result of the report
        data = self.pool.get('mis.report.instance').compute(
            self.cr, self.uid, objects[0].id, self.context)

        # Column headers
        header_name_list = ['']
        col_specs_template = {'': {'header': [1, 30, 'text', ''],
                                   'header_date': [1, 1, 'text', '']}}
        for col in data['header'][0]['cols']:
            col_specs_template[col['name']] = {'header': [1, 30, 'text',
                                                          col['name']],
                                               'header_date': [1, 1, 'text',
                                                               col['date']]}
            header_name_list.append(col['name'])
        c_specs = map(
            lambda x: self.render(x, col_specs_template, 'header'),
            header_name_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=self.rh_cell_style,
            set_column_size=True)
        c_specs = map(lambda x: self.render(
            x, col_specs_template, 'header_date'), header_name_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=self.rh_cell_style_date)

        ws.set_horz_split_pos(row_pos)
        ws.set_vert_split_pos(1)

        for line in data['content']:
            col = 0
            ws.write(row_pos, col, line['kpi_name'], self.mis_rh_cell_style)
            for value in line['cols']:
                col += 1
                num_format_str = '#'
                if value.get('dp'):
                    num_format_str += '.'
                    num_format_str += '0' * int(value['dp'])
                if value.get('prefix'):
                    num_format_str = '"%s"' % value['prefix'] + num_format_str
                if value.get('suffix'):
                    num_format_str += ' "%s"' % value['suffix']
                kpi_cell_style = xlwt.easyxf(
                    _xs['borders_all'] + _xs['right'],
                    num_format_str=num_format_str)
                if value.get('val'):
                    val = value['val']
                    if value.get('is_percentage'):
                        val = val / 0.01
                    ws.write(row_pos, col, val, kpi_cell_style)
                else:
                    ws.write(row_pos, col, value['val_r'], kpi_cell_style)
            row_pos += 1


MisBuilderXls('report.mis.report.instance.xls',
              'mis.report.instance',
              parser=MisBuilderXlsParser)
