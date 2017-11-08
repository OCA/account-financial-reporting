# -*- coding: utf-8 -*-
from datetime import datetime
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import _


class AccountStandardExcel(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, wizard):

        num_format = _('_ * #,##0.00_) ;_ * - #,##0.00_) ;_ * "-"??_) ;_ @_ ')
        bold = workbook.add_format({'bold': True})
        middle = workbook.add_format({'bold': True, 'top': 1})
        left = workbook.add_format({'left': 1, 'top': 1, 'bold': True})
        right = workbook.add_format({'right': 1, 'top': 1})
        top = workbook.add_format({'top': 1})
        currency_format = workbook.add_format({'num_format': _(num_format)})
        c_middle = workbook.add_format({'bold': True, 'top': 1, 'num_format': _(num_format)})
        report_format = workbook.add_format({'font_size': 24})
        rounding = self.env.user.company_id.currency_id.decimal_places or 2
        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format

        report = wizard.report_id

        def _get_data_float(data):
            if data == None or data == False:
                return 0.0
            else:
                return wizard.company_currency_id.round(data) + 0.0

        def get_date_format(date):
            if date:
                date = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
                date = date.strftime(date_format)
            return date

        def _header_sheet(sheet):
            sheet.write(0, 4, report.name, report_format)
            sheet.write(2, 0, _('Company:'), bold)
            sheet.write(3, 0, wizard.company_id.name,)
            sheet.write(4, 0, _('Print on %s') % report.print_time)

            sheet.write(2, 2, _('Start Date : %s ') % wizard.date_from if wizard.date_from else '')
            sheet.write(3, 2, _('End Date : %s ') % wizard.date_to if wizard.date_to else '')

            sheet.write(2, 4, _('Target Moves:'), bold)
            sheet.write(3, 4, _('All Entries') if wizard.target_move == 'all' else _('All Posted Entries'))

            sheet.write(2, 6, _('Only UnReconciled Entries') if wizard.reconciled is False else _('With Reconciled Entries'), bold)

        if wizard.type_ledger == 'aged':

            if wizard.summary:
                sheet = workbook.add_worksheet(report.name)
                _header_sheet(sheet)

                head = [
                    {'name': 'Code',
                     'larg': 10,
                     'col': {}},
                    {'name': 'Name',
                     'larg': 30,
                     'col': {}},
                    {'name': _('Not Due'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('0-30'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('30-60'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('60-90'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('90-120'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('Older'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('Total'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                ]

                all_lines = wizard._sql_get_line_for_report(type_l=('4_total',))
                # print(all_lines)
                if all_lines:

                    row = 6
                    row += 1
                    start_row = row
                    for i, line in enumerate(all_lines):
                        i += row
                        sheet.write(i, 0, line.get('code', ''))
                        sheet.write(i, 1, line.get('name', ''))
                        sheet.write(i, 2, _get_data_float(line.get('current')), currency_format)
                        sheet.write(i, 3, _get_data_float(line.get('age_30_days')), currency_format)
                        sheet.write(i, 4, _get_data_float(line.get('age_60_days')), currency_format)
                        sheet.write(i, 5, _get_data_float(line.get('age_90_days')), currency_format)
                        sheet.write(i, 6, _get_data_float(line.get('age_120_days')), currency_format)
                        sheet.write(i, 7, _get_data_float(line.get('older')), currency_format)
                        sheet.write(i, 8, _get_data_float(line.get('balance')), currency_format)
                    row = i

                    for j, h in enumerate(head):
                        sheet.set_column(j, j, h['larg'])

                    table = []
                    for h in head:
                        col = {}
                        col['header'] = h['name']
                        col.update(h['col'])
                        table.append(col)

                    sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
                                    {'total_row': 1,
                                     'columns': table,
                                     'style': 'Table Style Light 9',
                                     })

            else:  # aged not summary
                head = [
                    {'name': _('Date'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('JRNL'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('Account'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('Account Name'),
                     'larg': 15,
                     'col': {}},
                    {'name': _('Journal entries'),
                     'larg': 20,
                     'col': {}},
                    {'name': _('Ref'),
                     'larg': 40,
                     'col': {}},
                    {'name': _('Partner'),
                     'larg': 20,
                     'col': {}},
                    {'name': _('Due Date'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('Not Due'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('0-30'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('30-60'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('60-90'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('90-120'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('Older'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('Total'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('Match.'),
                     'larg': 10,
                     'col': {}},
                ]
                table = []
                for h in head:
                    col = {'header': h['name']}
                    col.update(h['col'])
                    table.append(col)

                def _set_line(line):
                    sheet.write(i, 0, get_date_format(line.get('date', '')))
                    sheet.write(i, 1, line.get('j_code', ''))
                    sheet.write(i, 2, line.get('a_code', ''))
                    sheet.write(i, 3, line.get('a_name', ''))
                    sheet.write(i, 4, line.get('move_name', ''))
                    sheet.write(i, 5, line.get('displayed_name', ''))
                    sheet.write(i, 6, line.get('partner_name', ''))
                    sheet.write(i, 7, get_date_format(line.get('date_maturity', '')))
                    sheet.write(i, 8, _get_data_float(line.get('current')), currency_format)
                    sheet.write(i, 9, _get_data_float(line.get('age_30_days')), currency_format)
                    sheet.write(i, 10, _get_data_float(line.get('age_60_days')), currency_format)
                    sheet.write(i, 11, _get_data_float(line.get('age_90_days')), currency_format)
                    sheet.write(i, 12, _get_data_float(line.get('age_120_days')), currency_format)
                    sheet.write(i, 13, _get_data_float(line.get('older')), currency_format)
                    sheet.write(i, 14, _get_data_float(line.get('balance')), currency_format)
                    sheet.write(i, 15, line.get('matching_number', ''))

                def _set_table(start_row, row):
                    sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
                                    {'total_row': 1,
                                     'columns': table,
                                     'style': 'Table Style Light 9',
                                     })
                    #sheet.write(row + 1, 10, "=I%s-J%s" % (row + 2, row + 2), currency_format)

                # With total workbook
                sheet = workbook.add_worksheet(report.name + _(' Totals'))
                _header_sheet(sheet)

                row = 6
                all_lines = wizard._sql_get_line_for_report(type_l=('1_init_line', '2_line'))
                for obj in report.report_object_ids:

                    lines_obj = []
                    obj_id = obj.id
                    for line in all_lines:
                        if line.get('report_object_id') == obj_id:
                            lines_obj.append(line)
                    if lines_obj:
                        row += 1
                        sheet.write(row, 0, obj.partner_id.name, left)  # obj.partner_id.name
                        sheet.write(row, 1, '', top)
                        sheet.write(row, 2, '', top)
                        sheet.write(row, 3, '', top)
                        sheet.write(row, 4, '', top)
                        sheet.write(row, 5, '', top)
                        sheet.write(row, 6, '', c_middle)
                        sheet.write(row, 7, '', c_middle)
                        sheet.write(row, 8, '', c_middle)
                        sheet.write(row, 9, '', c_middle)
                        sheet.write(row, 10, '', c_middle)
                        sheet.write(row, 11, '', c_middle)
                        sheet.write(row, 12, '', c_middle)
                        sheet.write(row, 13, '', c_middle)
                        sheet.write(row, 14, '', c_middle)
                        sheet.write(row, 15, '', right)

                        row += 2
                        start_row = row
                        for i, line in enumerate(lines_obj):
                            i += row
                            _set_line(line)

                        row = i

                        for j, h in enumerate(head):
                            sheet.set_column(j, j, h['larg'])

                        _set_table(start_row, row)
                        row += 2

                # Pivot
                sheet = workbook.add_worksheet(report.name)
                _header_sheet(sheet)

                # for group_by in data['group_by_data']['ids']:
                #     for line in data['lines_group_by'][group_by]['new_lines']:
                #         if line['type_line'] != 'total':
                #             all_lines.append(line)
                # Head
                if all_lines:
                    row = 6
                    row += 1
                    start_row = row
                    for i, line in enumerate(all_lines):
                        i += row
                        _set_line(line)
                    row = i

                    for j, h in enumerate(head):
                        sheet.set_column(j, j, h['larg'])

                    _set_table(start_row, row)

        else:  # standard report

            if wizard.summary:
                sheet = workbook.add_worksheet(report.name)
                _header_sheet(sheet)

                all_lines = wizard._sql_get_line_for_report(type_l=('4_total',))
                # for group_by in data['group_by_data']['ids']:
                #     all_lines.append(data['lines_group_by'][group_by])
                if all_lines:
                    # Head
                    head = [
                        {'name': 'Code',
                         'larg': 10,
                         'col': {}},
                        {'name': 'Name',
                         'larg': 30,
                         'col': {}},
                        {'name': 'Debit',
                         'larg': 15,
                         'col': {'total_function': 'sum', 'format': currency_format}},
                        {'name': 'Credit',
                         'larg': 15,
                         'col': {'total_function': 'sum', 'format': currency_format}},
                        {'name': 'Balance',
                         'larg': 15,
                         'col': {'total_function': 'sum', 'format': currency_format}},
                    ]

                    row = 6
                    row += 1
                    start_row = row
                    for i, line in enumerate(all_lines):
                        i += row
                        sheet.write(i, 0, line.get('code', ''))
                        sheet.write(i, 1, line.get('name', ''))
                        sheet.write(i, 2, line.get('debit', ''), currency_format)
                        sheet.write(i, 3, line.get('credit', ''), currency_format)
                        sheet.write(i, 4, line.get('balance', ''), currency_format)
                    row = i

                    for j, h in enumerate(head):
                        sheet.set_column(j, j, h['larg'])

                    table = []
                    for h in head:
                        col = {}
                        col['header'] = h['name']
                        col.update(h['col'])
                        table.append(col)

                    sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
                                    {'total_row': 1,
                                     'columns': table,
                                     'style': 'Table Style Light 9',
                                     })

            else:  # not summary

                head = [
                    {'name': _('Date'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('JRNL'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('Account'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('Account Name'),
                     'larg': 15,
                     'col': {}},
                    {'name': _('Journal entries'),
                     'larg': 20,
                     'col': {}},
                    {'name': _('Ref'),
                     'larg': 40,
                     'col': {}},
                    {'name': _('Partner'),
                     'larg': 20,
                     'col': {}},
                    {'name': _('Due Date'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('Debit'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('Credit'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('Balance'),
                     'larg': 15,
                     'col': {'format': currency_format}},
                    {'name': _('Match.'),
                     'larg': 10,
                     'col': {}},
                ]
                table = []
                for h in head:
                    col = {'header': h['name']}
                    col.update(h['col'])
                    table.append(col)

                def _set_line(line):
                    sheet.write(i, 0, get_date_format(line.get('date', '')) if line.get('type_view') != 'init' else 'INIT')
                    sheet.write(i, 1, line.get('j_code', ''))
                    sheet.write(i, 2, line.get('a_code', ''))
                    sheet.write(i, 3, line.get('a_name', ''))
                    sheet.write(i, 4, line.get('move_name', ''))
                    sheet.write(i, 5, line.get('displayed_name', ''))
                    sheet.write(i, 6, line.get('partner_name', ''))
                    sheet.write(i, 7, get_date_format(line.get('date_maturity', '')))
                    sheet.write(i, 8, _get_data_float(line.get('debit', '')), currency_format)
                    sheet.write(i, 9, _get_data_float(line.get('credit', '')), currency_format)
                    sheet.write(i, 10, _get_data_float(line.get('cumul_balance', '')), currency_format)
                    sheet.write(i, 11, line.get('matching_number', ''))

                def _set_table(start_row, row):
                    sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
                                    {'total_row': 1,
                                     'columns': table,
                                     'style': 'Table Style Light 9',
                                     })
                    #sheet.write(row + 1, 10, "=I%s-J%s" % (row + 2, row + 2), currency_format)

                # With total workbook
                sheet = workbook.add_worksheet(report.name + _(' Totals'))
                _header_sheet(sheet)

                row = 6

                all_lines = wizard._sql_get_line_for_report(type_l=('0_init', '1_init_line', '2_line'))
                for obj in report.report_object_ids:
                    lines_obj = []
                    obj_id = obj.id
                    for line in all_lines:
                        if line.get('report_object_id') == obj_id:
                            lines_obj.append(line)
                    if lines_obj:
                        row += 1
                        name_view = ''
                        if wizard.type == 'account':
                            name_view = obj.account_id.display_name
                        if wizard.type == 'partner':
                            name_view = obj.partner_id.display_name
                        if wizard.type == 'journal':
                            name_view = obj.journal_id.display_name

                        sheet.write(row, 0, name_view, left)
                        sheet.write(row, 1, '', top)
                        sheet.write(row, 2, '', top)
                        sheet.write(row, 3, '', top)
                        sheet.write(row, 4, '', top)
                        sheet.write(row, 5, '', top)
                        sheet.write(row, 6, '', top)
                        sheet.write(row, 7, '', top)
                        sheet.write(row, 8, '', top)
                        sheet.write(row, 9, '', top)
                        sheet.write(row, 10, '', top)
                        sheet.write(row, 11, '', right)

                        row += 2
                        start_row = row
                        for i, line in enumerate(lines_obj):
                            i += row
                            _set_line(line)

                        row = i

                        for j, h in enumerate(head):
                            sheet.set_column(j, j, h['larg'])

                        _set_table(start_row, row)
                        row += 2

                # Pivot workbook
                sheet = workbook.add_worksheet(report.name)
                _header_sheet(sheet)

                # Head
                if all_lines:
                    row = 6
                    row += 1
                    start_row = row
                    for i, line in enumerate(all_lines):
                        i += row
                        _set_line(line)
                    row = i

                    for j, h in enumerate(head):
                        sheet.set_column(j, j, h['larg'])

                    _set_table(start_row, row)


AccountStandardExcel('report.account_standard_report.report_account_standard_excel', 'account.report.standard.ledger')
