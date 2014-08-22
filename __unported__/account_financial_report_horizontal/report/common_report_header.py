# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.tools.translate import _


class common_report_header(object):

    def _get_start_date(self, data):
        if data.get('form', False) and data['form'].get('date_from', False):
            return data['form']['date_from']
        return ''

    def _get_target_move(self, data):
        if data.get('form', False) and data['form'].get('target_move', False):
            if data['form']['target_move'] == 'all':
                return _('All Entries')
            return _('All Posted Entries')
        return ''

    def _get_end_date(self, data):
        if data.get('form', False) and data['form'].get('date_to', False):
            return data['form']['date_to']
        return ''

    def get_start_period(self, data):
        if data.get('form', False) and data['form'].get('period_from', False):
            return self.pool['account.period'].browse(
                self.cr, self.uid,
                data['form']['period_from'][0]).name
        return ''

    def get_end_period(self, data):
        if data.get('form', False) and data['form'].get('period_to', False):
            return self.pool['account.period'].browse(
                self.cr, self.uid,
                data['form']['period_to'][0]).name
        return ''

    def _get_account(self, data):
        if data.get('form', False) and data['form'].get(
            'chart_account_id', False
        ):
            return self.pool['account.account'].browse(
                self.cr, self.uid,
                data['form']['chart_account_id'][0]).name
        return ''

    def _get_sortby(self, data):
        raise (_('Error'), _('Not implemented'))

    def _get_filter(self, data):
        if data.get('form', False) and data['form'].get('filter', False):
            if data['form']['filter'] == 'filter_date':
                return _('Date')
            elif data['form']['filter'] == 'filter_period':
                return _('Periods')
        return _('No Filter')

    def _get_fiscalyear(self, data):
        if data.get('form', False) and data['form'].get(
            'fiscalyear_id', False
        ):
            return self.pool['account.fiscalyear'].browse(
                self.cr, self.uid,
                data['form']['fiscalyear_id'][0]).name
        return ''
