# -*- coding: utf-8 -*-
##############################################################################
#
#    account_financial_report_webkit module for OpenERP, Webkit based
#    extended report financial report
#    Copyright (C) 2012 SYLEAM Info Services (<http://www.syleam.fr/>)
#              Sebastien LANGE <sebastien.lange@syleam.fr>
#
#    This file is a part of account_financial_report_webkit
#
#    account_financial_report_webkit is free software: you can redistribute it
#    and/or modify it under the terms of the GNU Affero General Public License
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    account_financial_report_webkit is distributed in the hope that it will be
#    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.modules.registry import RegistryManager
from datetime import datetime

from .common_reports import CommonReportHeaderWebkit
from .webkit_parser_header_fix import HeaderFooterTextWebKitParser


class PrintJournalWebkit(report_sxw.rml_parse, CommonReportHeaderWebkit):

    # pylint: disable=old-api7-method-defined
    def __init__(self, cursor, uid, name, context):
        super(PrintJournalWebkit, self).__init__(cursor, uid, name,
                                                 context=context)
        self.pool = RegistryManager.get(self.cr.dbname)
        self.cursor = self.cr

        company_obj = self.pool.get('res.company')

        company_id = company_obj._company_default_get(self.cr, uid,
                                                      'res.users',
                                                      context=context)
        company = company_obj.browse(self.cr, uid, company_id, context=context)
        header_report_name = ' - '.join((_('JOURNALS'), company.name,
                                         company.currency_id.name))

        footer_date_time = self.formatLang(str(datetime.today()),
                                           date_time=True)

        self.localcontext.update({
            'cr': cursor,
            'uid': uid,
            'report_name': _('Journals'),
            'display_account_raw': self._get_display_account_raw,
            'filter_form': self._get_filter,
            'target_move': self._get_target_move,
            'initial_balance': self._get_initial_balance,
            'amount_currency': self._get_amount_currency,
            'display_partner_account': self._get_display_partner_account,
            'display_target_move': self._get_display_target_move,
            'journals': self._get_journals_br,
            'additional_args': [
                ('--header-font-name', 'Helvetica'),
                ('--footer-font-name', 'Helvetica'),
                ('--header-font-size', '10'),
                ('--footer-font-size', '6'),
                ('--header-left', header_report_name),
                ('--header-spacing', '2'),
                ('--footer-left', footer_date_time),
                ('--footer-right', ' '.join((_('Page'), '[page]', _('of'),
                                             '[topage]'))),
                ('--footer-line',),
            ],
        })

    def set_context(self, objects, data, ids, report_type=None):
        """Populate a ledger_lines attribute on each browse record that will
           be used by mako template"""

        # Reading form
        main_filter = self._get_form_param('filter', data, default='filter_no')
        target_move = self._get_form_param('target_move', data, default='all')
        start_date = self._get_form_param('date_from', data)
        stop_date = self._get_form_param('date_to', data)
        start_period = self.get_start_period_br(data)
        stop_period = self.get_end_period_br(data)
        fiscalyear = self.get_fiscalyear_br(data)
        journal_ids = self._get_form_param('journal_ids', data)
        chart_account = self._get_chart_account_id_br(data)
        account_period_obj = self.pool.get('account.period')

        domain = [('journal_id', 'in', journal_ids)]
        if main_filter == 'filter_no':
            domain += [
                ('date', '>=',
                    self.get_first_fiscalyear_period(fiscalyear).date_start),
                ('date', '<=',
                    self.get_last_fiscalyear_period(fiscalyear).date_stop),
            ]
        # computation of move lines
        elif main_filter == 'filter_date':
            domain += [
                ('date', '>=', start_date),
                ('date', '<=', stop_date),
            ]
        elif main_filter == 'filter_period':
            period_ids = account_period_obj.build_ctx_periods(self.cursor,
                                                              self.uid,
                                                              start_period.id,
                                                              stop_period.id)
            domain = [
                ('period_id', 'in', period_ids),
            ]
        if target_move == 'posted':
            domain += [('state', '=', 'posted')]
        account_journal_period_obj = self.pool.get('account.journal.period')
        new_ids = account_journal_period_obj.search(self.cursor, self.uid, [
            ('journal_id', 'in', journal_ids),
            ('period_id', 'in', period_ids),
        ])
        objects = account_journal_period_obj.browse(self.cursor, self.uid,
                                                    new_ids)
        # Sort by journal and period
        objects.sorted(key=lambda a: (a.journal_id.code,
                                      a.period_id.date_start))
        move_obj = self.pool.get('account.move')
        moves = {}
        for journal_period in objects:
            domain_arg = [
                ('journal_id', '=', journal_period.journal_id.id),
                ('period_id', '=', journal_period.period_id.id),
            ]
            if target_move == 'posted':
                domain_arg += [('state', '=', 'posted')]
            move_ids = move_obj.search(self.cursor, self.uid, domain_arg,
                                       order="name")
            moves[journal_period.id] = move_obj.browse(self.cursor, self.uid,
                                                       move_ids)
            # Sort account move line by account accountant
            for move in moves[journal_period.id]:
                move.line_id.sorted(key=lambda a: (a.date, a.account_id.code))

        self.localcontext.update({
            'fiscalyear': fiscalyear,
            'start_date': start_date,
            'stop_date': stop_date,
            'start_period': start_period,
            'stop_period': stop_period,
            'chart_account': chart_account,
            'moves': moves,
        })

        return super(PrintJournalWebkit, self).set_context(
            objects, data, new_ids, report_type=report_type)


HeaderFooterTextWebKitParser(
    'report.account.account_report_print_journal_webkit',
    'account.journal.period',
    'addons/account_financial_report_webkit/report/templates/\
    account_report_print_journal.mako',
    parser=PrintJournalWebkit)
