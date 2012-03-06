# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright Camptocamp SA 2011
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

import pooler

from report import report_sxw
from tools.translate import _
from datetime import datetime
from common_balance_reports import CommonBalanceReportHeaderWebkit
from webkit_parser_header_fix import HeaderFooterTextWebKitParser


class ProfitLossWebkit(report_sxw.rml_parse, CommonBalanceReportHeaderWebkit):

    def __init__(self, cursor, uid, name, context):
        super(ProfitLossWebkit, self).__init__(cursor, uid, name, context=context)
        self.pool = pooler.get_pool(self.cr.dbname)
        self.cursor = self.cr
        
        company = self.pool.get('res.users').browse(self.cr, uid, uid, context=context).company_id
        header_report_name = ' - '.join((_('PROFIT AND LOSS'), company.name, company.currency_id.name))

        footer_date_time = self.formatLang(str(datetime.today()), date_time=True)

        self.localcontext.update({
            'cr': cursor,
            'uid': uid,
            'report_name': _('Profit and Loss'),
            'display_account': self._get_display_account,
            'display_account_raw': self._get_display_account_raw,
            'filter_form': self._get_filter,
            'target_move': self._get_target_move,
            'display_target_move': self._get_display_target_move,
            'accounts': self._get_accounts_br,
            'numbers_display': self._get_numbers_display,
            'level_print': self._get_level_print,
            'level_bold': self._get_level_bold,
            'level_italic': self._get_level_italic,
            'level_size': self._get_level_size,
            'level_underline': self._get_level_underline,
            'level_uppercase': self._get_level_uppercase,
            'additional_args': [
                ('--header-font-name', 'Helvetica'),
                ('--footer-font-name', 'Helvetica'),
                ('--header-font-size', '10'),
                ('--footer-font-size', '6'),
                ('--header-left', header_report_name),
                ('--header-spacing', '2'),
                ('--footer-left', footer_date_time),
                ('--footer-right', ' '.join((_('Page'), '[page]', _('of'), '[topage]'))),
                ('--footer-line',),
            ],
        })

    def _get_level_print(self, data, level):
        return self._get_form_param("level%s_print" % (level,), data)

    def _get_level_bold(self, data, level):
        return self._get_form_param("level%s_bold" % (level,), data)

    def _get_level_italic(self, data, level):
        return self._get_form_param("level%s_italic" % (level,), data)

    def _get_level_size(self, data, level):
        return self._get_form_param("level%s_size" % (level,), data)

    def _get_level_underline(self, data, level):
        return self._get_form_param("level%s_underline" % (level,), data)

    def _get_level_uppercase(self, data, level):
        return self._get_form_param("level%s_uppercase" % (level,), data)

    def _update_levels(self, objects):
        # start leveling from 0
        levels = [account['current']['level'] for account in objects]
        min_level = min(levels)

        for account in objects:
            account['current']['level'] -= min_level
        return objects

    def set_context(self, objects, data, ids, report_type=None):
        """Populate a ledger_lines attribute on each browse record that will be used
        by mako template"""
        objects, new_ids, context_report_values = self.compute_balance_data(data, filter_report_type=['expense', 'income'])

        objects = self._update_levels(objects)

        self.localcontext.update(context_report_values)

        return super(ProfitLossWebkit, self).set_context(objects, data, new_ids,
                                                            report_type=report_type)

HeaderFooterTextWebKitParser('report.account.account_report_profit_loss_webkit',
                             'account.account',
                             'addons/account_financial_report_webkit/report/templates/account_report_profit_loss.mako',
                             parser=ProfitLossWebkit)
