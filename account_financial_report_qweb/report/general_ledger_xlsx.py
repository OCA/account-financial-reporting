# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw

from ..wizard.ledger_report_wizard import FIELDS_TO_READ

_logger = logging.getLogger(__name__)

FIELDS_TO_READ_INV = {v: k for k, v in FIELDS_TO_READ.iteritems()}


class GeneralLedgerXslx(ReportXlsx):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(GeneralLedgerXslx, self).__init__(
            name, table, rml, parser, header, store)

    def generate_xlsx_report(self, workbook, data, objects):

        data = objects.compute()
        report_name = data['header'][0].get('title', 'GeneralLedgerXslx')
        sheet = workbook.add_worksheet(report_name[:31])
        row_pos = 0
        col_pos = 0

        sheet.set_column(col_pos, col_pos, 30)
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format({'bold': True,
                                             'align': 'center',
                                             'border': True,
                                             'bg_color': '#FFFFCC'})
        std_cell_format = workbook.add_format({'bold': False,
                                               'align': 'left',
                                               'border': False,
                                               'bg_color': '#FFFFFF'})
        # write report title on first cell A0 in XLSX sheet
        sheet.write(row_pos, 0, report_name, bold)
        row_pos += 2

        # write filters taken for this report
        col = 1
        for k, v in data['header'][0].get('filters').iteritems():
            sheet.write(row_pos, col, k, header_format)
            sheet.write(row_pos+1, col, v, header_format)
            col += 2

        row_pos += 5

        # write header line
        col = 0
        content = data['content'][0]

        header_done = False
        sorted_acc = content.keys()
        sorted_acc.sort()
        for acc in sorted_acc:
            for move_lines in content[acc]:
                # write line with account name
                # sheet.write(row_pos, col+1, acc, bold)
                # row_pos += 1
                # write column headers
                if not header_done:
                    for k, v in move_lines.iteritems():
                        position = FIELDS_TO_READ_INV.get(k, 'remove')
                        if position == 'remove':
                            continue
                        sheet.write(row_pos, position, k, bold)
                        # col2 += 1
                    row_pos += 1
                    header_done = True

                for k, v in move_lines.iteritems():
                    if isinstance(v, (list, tuple)):
                        v = v[1]
                    position = FIELDS_TO_READ_INV.get(k, 'remove')
                    if position == 'remove':
                        continue
                    if position == 0:
                        sheet.write(row_pos, position, v, bold)
                    else:
                        sheet.write(row_pos, position, v, std_cell_format)

                    # col2 += 1
                row_pos += 1


GeneralLedgerXslx('report.ledger.report.wizard.xlsx',
                  'ledger.report.wizard', parser=report_sxw.rml_parse)
