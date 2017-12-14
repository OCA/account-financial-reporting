# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import _, exceptions, models, fields
from openerp.addons.account.wizard.account_report_common_journal \
    import account_common_journal_report
import logging
_logger = logging.getLogger(__name__)


class AccountPrintJournalXls(models.TransientModel):
    _inherit = 'account.print.journal'
    _name = 'account.print.journal.xls'
    _description = 'Print/Export Journal'

    journal_ids = fields.Many2many(
        'account.journal',
        'account_print_journal_xls_journal_rel',
        'journal_xls_id',
        'journal_id',
        string='Journals',
        required=True
    )
    group_entries = fields.Boolean(
        'Group Entries', default=True,
        help="Group entries with same General Account & Tax Code."
    )

    # pylint: disable=old-api7-method-defined
    def fields_get(self, cr, uid, fields=None, context=None):
        res = super(AccountPrintJournalXls, self).fields_get(
            cr, uid, fields, context)
        if context.get('print_by') == 'fiscalyear':
            if 'fiscalyear_id' in res:
                res['fiscalyear_id']['required'] = True
            if 'period_from' in res:
                res['period_from']['readonly'] = True
            if 'period_to' in res:
                res['period_to']['readonly'] = True
        else:
            if 'period_from' in res:
                res['period_from']['required'] = True
            if 'period_to' in res:
                res['period_to']['required'] = True
        return res

    # pylint: disable=old-api7-method-defined
    def fy_period_ids(self, cr, uid, fiscalyear_id):
        """ returns all periods from a fiscalyear sorted by date """
        fy_period_ids = []
        cr.execute('''
                   SELECT id, coalesce(special, False) AS special
                   FROM account_period
                   WHERE fiscalyear_id=%s ORDER BY date_start, special DESC''',
                   (fiscalyear_id,))
        res = cr.fetchall()
        if res:
            fy_period_ids = [x[0] for x in res]
        return fy_period_ids

    # pylint: disable=old-api7-method-defined
    def onchange_fiscalyear_id(self, cr, uid, ids, fiscalyear_id=False,
                               context=None):
        res = {'value': {}}
        if context.get('print_by') == 'fiscalyear':
            # get period_from/to with opening/close periods
            fy_period_ids = self.fy_period_ids(cr, uid, fiscalyear_id)
            if fy_period_ids:
                res['value']['period_from'] = fy_period_ids[0]
                res['value']['period_to'] = fy_period_ids[-1]
        return res

    # pylint: disable=old-api7-method-defined
    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """ skip account.common.journal.report,fields_view_get
        (adds domain filter on journal type)  """
        return super(account_common_journal_report, self).\
            fields_view_get(cr, uid, view_id, view_type, context, toolbar,
                            submenu)

    # pylint: disable=old-api7-method-defined
    def xls_export(self, cr, uid, ids, context=None):
        return self.print_report(cr, uid, ids, context=context)

    # pylint: disable=old-api7-method-defined
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        move_obj = self.pool.get('account.move')
        print_by = context.get('print_by')
        wiz_form = self.browse(cr, uid, ids)[0]
        fiscalyear_id = wiz_form.fiscalyear_id.id
        company_id = wiz_form.company_id.id

        if print_by == 'fiscalyear':
            wiz_period_ids = self.fy_period_ids(cr, uid, fiscalyear_id)
        else:
            period_from = wiz_form.period_from
            period_to = wiz_form.period_to
            cr.execute("""
                SELECT id, coalesce(special, False) AS special
                FROM account_period ap
                WHERE ap.date_start>=%s AND ap.date_stop<=%s AND company_id=%s
                ORDER BY date_start, special DESC""",
                       (period_from.date_start,
                        period_to.date_stop,
                        company_id))
            wiz_period_ids = map(lambda x: x[0], cr.fetchall())
        wiz_journal_ids = [j.id for j in wiz_form.journal_ids]

        # sort journals
        cr.execute('SELECT id FROM account_journal '
                   'WHERE id IN %s ORDER BY type DESC',
                   (tuple(wiz_journal_ids),))
        wiz_journal_ids = map(lambda x: x[0], cr.fetchall())

        datas = {
            'model': 'account.journal',
            'print_by': print_by,
            'sort_selection': wiz_form.sort_selection,
            'target_move': wiz_form.target_move,
            'display_currency': wiz_form.amount_currency,
            'group_entries': wiz_form.group_entries,
        }

        if wiz_form.target_move == 'posted':
            move_states = ['posted']
        else:
            move_states = ['draft', 'posted']

        if print_by == 'fiscalyear':
            journal_fy_ids = []
            for journal_id in wiz_journal_ids:
                aml_ids = move_obj.search(cr, uid,
                                          [('journal_id', '=', journal_id),
                                           ('period_id', 'in', wiz_period_ids),
                                           ('state', 'in', move_states)],
                                          limit=1)
                if aml_ids:
                    journal_fy_ids.append((journal_id, fiscalyear_id))
            if not journal_fy_ids:
                raise exceptions.except_orm(
                    _('No Data Available'),
                    _('No records found for your selection!'))
            datas.update({
                'ids': [x[0] for x in journal_fy_ids],
                'journal_fy_ids': journal_fy_ids,
            })
        else:
            # perform account.move.line query in stead of
            # 'account.journal.period' since this table is not always reliable
            journal_period_ids = []
            for journal_id in wiz_journal_ids:
                period_ids = []
                for period_id in wiz_period_ids:
                    aml_ids = move_obj.search(cr, uid,
                                              [('journal_id', '=', journal_id),
                                               ('period_id', '=', period_id),
                                               ('state', 'in', move_states)],
                                              limit=1)
                    if aml_ids:
                        period_ids.append(period_id)
                if period_ids:
                    journal_period_ids.append((journal_id, period_ids))
            if not journal_period_ids:
                raise exceptions.except_orm(
                    _('No Data Available'),
                    _('No records found for your selection!'))
            datas.update({
                'ids': [x[0] for x in journal_period_ids],
                'journal_period_ids': journal_period_ids,
            })

        if context.get('xls_export'):
            return {'type': 'ir.actions.report.xml',
                    'report_name': 'nov.account.journal.xls',
                    'datas': datas}
        else:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'nov.account.journal.print',
                'datas': datas}
