# -*- coding: utf-8 -*-
##############################################################################
#
#    mis_builder module for Odoo, Management Information System Builder
#    Copyright (C) 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
#
#    This file is a part of mis_builder
#
#    mis_builder is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    mis_builder is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw
import logging
_logger = logging.getLogger(__name__)


class MisBuilderXslx(ReportXlsx):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(MisBuilderXslx, self).__init__(
            name, table, rml, parser, header, store)

    def generate_xlsx_report(self, workbook, data, objects):

        report_name = objects[0].name
        sheet = workbook.add_worksheet(report_name[:31])
        row_pos = 0
        col_pos = 0

        sheet.set_column(col_pos, col_pos, 30)
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format({'bold': True,
                                             'align': 'center',
                                             'border': True,
                                             'bg_color': '#FFFFCC'})
        kpi_name_format = workbook.add_format({'bold': True,
                                               'border': True,
                                               'bg_color': '#FFFFCC'})
        sheet.write(row_pos, 0, report_name, bold)
        row_pos += 1
        col_pos += 1

        # get the computed result of the report
        data = objects.compute()

        # Column headers
        for col in data['header'][0]['cols']:
            sheet.set_column(col_pos, col_pos, 30)
            sheet.write(row_pos, col_pos, col['name'], header_format)
            sheet.write(row_pos+1, col_pos, col['date'], header_format)
            col_pos += 1
        row_pos += 2
        for line in data['content']:
            col = 0
            sheet.write(row_pos, col, line['kpi_name'], kpi_name_format)
            for value in line['cols']:
                col += 1
                num_format_str = '#'
                if value.get('dp'):
                    num_format_str += '.'
                    num_format_str += '0' * int(value['dp'])
                if value.get('prefix'):
                    num_format_str = '"%s"' % value['prefix'] + num_format_str
                if value.get('suffix'):
                    num_format_str = num_format_str + ' "%s"' % value['suffix']
                kpi_format = workbook.add_format({'num_format': num_format_str,
                                                  'border': 1,
                                                  'align': 'right'})
                if value.get('val'):
                    val = value['val']
                    if value.get('is_percentage'):
                        val = val / 0.01
                    sheet.write(row_pos, col, val, kpi_format)
                else:
                    sheet.write(row_pos, col, value['val_r'], kpi_format)
            row_pos += 1


MisBuilderXslx('report.mis.report.instance.xlsx',
               'mis.report.instance', parser=report_sxw.rml_parse)
