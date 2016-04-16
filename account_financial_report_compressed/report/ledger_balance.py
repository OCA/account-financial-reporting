# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Matthieu Dietrich
#    Copyright Camptocamp SA 2014
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
from datetime import datetime

from openerp.report import report_sxw
from openerp import pooler
from openerp.tools.translate import _
from openerp.addons.account_financial_report_webkit.\
    report.common_reports import CommonReportHeaderWebkit
from openerp.addons.account_financial_report_webkit.\
    report.webkit_parser_header_fix import HeaderFooterTextWebKitParser


class LedgerBalanceWebkit(report_sxw.rml_parse, CommonReportHeaderWebkit):

    def __init__(self, cursor, uid, name, context):
        super(LedgerBalanceWebkit, self).__init__(
            cursor, uid, name, context=context
        )
        self.pool = pooler.get_pool(self.cr.dbname)
        self.cursor = self.cr

        company = self.pool.get('res.users').browse(
            self.cr, uid, uid, context=context
        ).company_id
        header_report_name = ' - '.join((_('LEDGER BALANCE'),
                                        company.name,
                                        company.currency_id.name))

        footer_date_time = self.formatLang(str(datetime.today()),
                                           date_time=True)

        self.localcontext.update({
            'cr': cursor,
            'uid': uid,
            'report_name': _('Ledger Balance'),
            'display_account': self._get_display_account,
            'display_account_raw': self._get_display_account_raw,
            'filter_form': self._get_filter,
            'target_move': self._get_target_move,
            'initial_balance': self._get_initial_balance,
            'amount_currency': self._get_amount_currency,
            'display_target_move': self._get_display_target_move,
            'accounts': self._get_accounts_br,
            'additional_args': [
                ('--header-font-name', 'Helvetica'),
                ('--footer-font-name', 'Helvetica'),
                ('--header-font-size', '10'),
                ('--footer-font-size', '6'),
                ('--header-left', header_report_name),
                ('--header-spacing', '2'),
                ('--footer-left', footer_date_time),
                ('--footer-right', ' '.join(
                    (_('Page'), '[page]', _('of'), '[topage]'))),
                ('--footer-line',),
            ],
        })

    def setLang(self, lang):
        self.localcontext['lang'] = lang
        self.lang_dict_called = False

HeaderFooterTextWebKitParser(
    'report.account.account_report_ledger_balance_webkit',
    'account.account',
    'addons/account_financial_report_compressed/'
    'report/templates/account_report_ledger_balance.mako',
    parser=LedgerBalanceWebkit)
