# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011 Camptocamp SA (http://www.camptocamp.com)
#
# Author: Guewen Baconnier (Camptocamp)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import time

from lxml import etree
from datetime import datetime
from openerp.osv import fields, orm
from openerp.tools.translate import _


def previous_year_date(date, nb_prev=1):
    if not date:
        return False
    parsed_date = datetime.strptime(date, '%Y-%m-%d')
    previous_date = datetime(year=parsed_date.year - nb_prev,
                             month=parsed_date.month,
                             day=parsed_date.day)
    return previous_date


class AccountBalanceCommonWizard(orm.TransientModel):

    """Will launch trial balance report and pass required args"""

    _inherit = "account.common.account.report"
    _name = "account.common.balance.report"
    _description = "Common Balance Report"

    # an update module should be done if changed
    # in order to create fields in db
    COMPARISON_LEVEL = 3

    COMPARE_SELECTION = [('filter_no', 'No Comparison'),
                         ('filter_year', 'Fiscal Year'),
                         ('filter_date', 'Date'),
                         ('filter_period', 'Periods'),
                         ('filter_opening', 'Opening Only')]

    M2O_DYNAMIC_FIELDS = [f % index for f in ["comp%s_fiscalyear_id",
                                              "comp%s_period_from",
                                              "comp%s_period_to"]
                          for index in range(COMPARISON_LEVEL)]
    SIMPLE_DYNAMIC_FIELDS = [f % index for f in ["comp%s_filter",
                                                 "comp%s_date_from",
                                                 "comp%s_date_to"]
                             for index in range(COMPARISON_LEVEL)]
    DYNAMIC_FIELDS = M2O_DYNAMIC_FIELDS + SIMPLE_DYNAMIC_FIELDS

    def _get_account_ids(self, cr, uid, context=None):
        res = False
        if context.get('active_model', False) == 'account.account' \
                and context.get('active_ids', False):
            res = context['active_ids']
        return res

    _columns = {
        'account_ids': fields.many2many(
            'account.account', string='Filter on accounts',
            help="Only selected accounts will be printed. Leave empty to \
            print all accounts."),
        'filter': fields.selection(
            [('filter_no', 'No Filters'),
             ('filter_date', 'Date'),
             ('filter_period', 'Periods'),
             ('filter_opening', 'Opening Only')],
            "Filter by",
            required=True,
            help='Filter by date: no opening balance will be displayed. '
            '(opening balance can only be computed based on period to be \
            correct).'),
        # Set statically because of the impossibility of changing the selection
        # field when changing chart_account_id
        'account_level': fields.selection(
            [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
             ('6', '6')], string="Account level"),
    }

    for index in range(COMPARISON_LEVEL):
        _columns.update(
            {"comp%s_filter" % index:
                fields.selection(
                    COMPARE_SELECTION, string='Compare By', required=True),
             "comp%s_fiscalyear_id" % index:
                fields.many2one('account.fiscalyear', 'Fiscal Year'),
             "comp%s_period_from" % index:
                fields.many2one('account.period', 'Start Period'),
             "comp%s_period_to" % index:
                fields.many2one('account.period', 'End Period'),
             "comp%s_date_from" % index:
                fields.date("Start Date"),
             "comp%s_date_to" % index:
                fields.date("End Date")})

    _defaults = {
        'account_ids': _get_account_ids,
    }

    def _check_fiscalyear(self, cr, uid, ids, context=None):
        obj = self.read(
            cr, uid, ids[0], ['fiscalyear_id', 'filter'], context=context)
        if not obj['fiscalyear_id'] and obj['filter'] == 'filter_no':
            return False
        return True

    _constraints = [
        (_check_fiscalyear,
         'When no Fiscal year is selected, you must choose to filter by \
         periods or by date.', ['filter']),
    ]

    def default_get(self, cr, uid, fields, context=None):
        """
             To get default values for the object.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param fields: List of fields for which we want default values
             @param context: A standard dictionary

             @return: A dictionary which of fields with values.

        """
        res = super(AccountBalanceCommonWizard, self).default_get(
            cr, uid, fields, context=context)
        for index in range(self.COMPARISON_LEVEL):
            field = "comp%s_filter" % (index,)
            if not res.get(field, False):
                res[field] = 'filter_no'
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        res = super(AccountBalanceCommonWizard, self).fields_view_get(
            cr, uid, view_id, view_type, context=context, toolbar=toolbar,
            submenu=submenu)

        res['fields'].update(self.fields_get(cr, uid,
                             allfields=self.DYNAMIC_FIELDS,
                             context=context, write_access=True))

        eview = etree.fromstring(res['arch'])
        placeholder = eview.xpath("//page[@name='placeholder']")
        if placeholder:
            placeholder = placeholder[0]
            for index in range(self.COMPARISON_LEVEL):
                page = etree.Element(
                    'page',
                    {'name': "comp%s" % index,
                     'string': _("Comparison %s") % (index + 1, )})
                group = etree.Element('group')
                page.append(group)

                def modifiers_and_append(elem):
                    orm.setup_modifiers(elem)
                    group.append(elem)

                modifiers_and_append(etree.Element(
                    'field',
                    {'name': "comp%s_filter" % index,
                     'on_change': "onchange_comp_filter(%(index)s, filter,\
                     comp%(index)s_filter, fiscalyear_id, date_from, date_to)"
                     % {'index': index}}))
                modifiers_and_append(etree.Element(
                    'field',
                    {'name': "comp%s_fiscalyear_id" % index,
                     'attrs':
                     "{'required': [('comp%(index)s_filter','in',\
                     ('filter_year','filter_opening'))],"
                     " 'invisible': [('comp%(index)s_filter','not in',\
                     ('filter_year','filter_opening'))]}" % {'index': index}}))

                dates_attrs = "{'required': [('comp%(index)s_filter','=',\
                                                        'filter_date')], " \
                              " 'invisible': [('comp%(index)s_filter','!=',\
                                                        'filter_date')]}" % {
                    'index': index}
                modifiers_and_append(etree.Element(
                    'separator',
                    {'string': _('Dates'),
                     'colspan': '4',
                     'attrs': dates_attrs}))
                modifiers_and_append(etree.Element(
                    'field',
                    {'name': "comp%s_date_from" % index,
                     'attrs': dates_attrs}))
                modifiers_and_append(etree.Element(
                    'field',
                    {'name': "comp%s_date_to" % index,
                     'attrs': dates_attrs}))

                periods_attrs = "{'required': [('comp%(index)s_filter','=',\
                                                        'filter_period')]," \
                                " 'invisible': [('comp%(index)s_filter','!=',\
                                                        'filter_period')]}" % {
                    'index': index}
                periods_domain = "[('special', '=', False)]"
                modifiers_and_append(etree.Element(
                    'separator',
                    {'string': _('Periods'),
                     'colspan': '4',
                     'attrs': periods_attrs}))
                modifiers_and_append(etree.Element(
                    'field',
                    {'name': "comp%s_period_from" % index,
                     'attrs': periods_attrs,
                     'domain': periods_domain}))
                modifiers_and_append(etree.Element(
                    'field',
                    {'name': "comp%s_period_to" % index,
                     'attrs': periods_attrs,
                     'domain': periods_domain}))

                placeholder.addprevious(page)
            placeholder.getparent().remove(placeholder)
        res['arch'] = etree.tostring(eview)
        return res

    def onchange_filter(self, cr, uid, ids, filter='filter_no',
                        fiscalyear_id=False, context=None):
        res = {}
        if filter == 'filter_no':
            res['value'] = {'period_from': False,
                            'period_to': False,
                            'date_from': False,
                            'date_to': False}
        if filter == 'filter_date':
            if fiscalyear_id:
                fyear = self.pool.get('account.fiscalyear').browse(
                    cr, uid, fiscalyear_id, context=context)
                date_from = fyear.date_start
                date_to = fyear.date_stop > time.strftime(
                    '%Y-%m-%d') and time.strftime('%Y-%m-%d') \
                    or fyear.date_stop
            else:
                date_from, date_to = time.strftime(
                    '%Y-01-01'), time.strftime('%Y-%m-%d')
            res['value'] = {'period_from': False, 'period_to':
                            False, 'date_from': date_from, 'date_to': date_to}
        if filter == 'filter_period' and fiscalyear_id:
            start_period = end_period = False
            cr.execute('''
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f
                                   ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND COALESCE(p.special, FALSE) = FALSE
                               ORDER BY p.date_start ASC
                               LIMIT 1) AS period_start
                UNION ALL
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f
                                   ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND p.date_start < NOW()
                               AND COALESCE(p.special, FALSE) = FALSE
                               ORDER BY p.date_stop DESC
                               LIMIT 1) AS period_stop''',
                       (fiscalyear_id, fiscalyear_id))
            periods = [i[0] for i in cr.fetchall()]
            if periods:
                start_period = end_period = periods[0]
                if len(periods) > 1:
                    end_period = periods[1]
            res['value'] = {'period_from': start_period, 'period_to':
                            end_period, 'date_from': False, 'date_to': False}
        return res

    def onchange_comp_filter(self, cr, uid, ids, index,
                             main_filter='filter_no', comp_filter='filter_no',
                             fiscalyear_id=False, start_date=False,
                             stop_date=False, context=None):
        res = {}
        fy_obj = self.pool.get('account.fiscalyear')
        last_fiscalyear_id = False
        if fiscalyear_id:
            fiscalyear = fy_obj.browse(cr, uid, fiscalyear_id, context=context)
            last_fiscalyear_ids = fy_obj.search(
                cr, uid, [('date_stop', '<', fiscalyear.date_start)],
                limit=self.COMPARISON_LEVEL, order='date_start desc',
                context=context)
            if last_fiscalyear_ids:
                if len(last_fiscalyear_ids) > index:
                    # first element for the comparison 1, second element for
                    # the comparison 2
                    last_fiscalyear_id = last_fiscalyear_ids[index]

        fy_id_field = "comp%s_fiscalyear_id" % (index,)
        period_from_field = "comp%s_period_from" % (index,)
        period_to_field = "comp%s_period_to" % (index,)
        date_from_field = "comp%s_date_from" % (index,)
        date_to_field = "comp%s_date_to" % (index,)

        if comp_filter == 'filter_no':
            res['value'] = {
                fy_id_field: False,
                period_from_field: False,
                period_to_field: False,
                date_from_field: False,
                date_to_field: False
            }
        if comp_filter in ('filter_year', 'filter_opening'):
            res['value'] = {
                fy_id_field: last_fiscalyear_id,
                period_from_field: False,
                period_to_field: False,
                date_from_field: False,
                date_to_field: False
            }
        if comp_filter == 'filter_date':
            dates = {}
            if main_filter == 'filter_date':
                dates = {
                    'date_start': previous_year_date(start_date, index + 1).
                    strftime('%Y-%m-%d'),
                    'date_stop': previous_year_date(stop_date, index + 1).
                    strftime('%Y-%m-%d'),
                }
            elif last_fiscalyear_id:
                dates = fy_obj.read(
                    cr, uid, last_fiscalyear_id, ['date_start', 'date_stop'],
                    context=context)

            res['value'] = {fy_id_field: False,
                            period_from_field: False,
                            period_to_field: False,
                            date_from_field: dates.get('date_start', False),
                            date_to_field: dates.get('date_stop', False)}
        if comp_filter == 'filter_period' and last_fiscalyear_id:
            start_period = end_period = False
            cr.execute('''
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f
                                   ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %(fiscalyear)s
                               AND COALESCE(p.special, FALSE) = FALSE
                               ORDER BY p.date_start ASC
                               LIMIT 1) AS period_start
                UNION ALL
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f
                                   ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %(fiscalyear)s
                               AND p.date_start < NOW()
                               AND COALESCE(p.special, FALSE) = FALSE
                               ORDER BY p.date_stop DESC
                               LIMIT 1) AS period_stop''',
                       {'fiscalyear': last_fiscalyear_id})
            periods = [i[0] for i in cr.fetchall()]
            if periods and len(periods) > 1:
                start_period = end_period = periods[0]
                if len(periods) > 1:
                    end_period = periods[1]
            res['value'] = {fy_id_field: False,
                            period_from_field: start_period,
                            period_to_field: end_period,
                            date_from_field: False,
                            date_to_field: False}
        return res

    def pre_print_report(self, cr, uid, ids, data, context=None):
        data = super(AccountBalanceCommonWizard, self).pre_print_report(
            cr, uid, ids, data, context=context)
        if context is None:
            context = {}

        # will be used to attach the report on the main account
        data['ids'] = [data['form']['chart_account_id']]

        fields_to_read = ['account_ids', 'account_level']
        fields_to_read += self.DYNAMIC_FIELDS
        vals = self.read(cr, uid, ids, fields_to_read, context=context)[0]

        # extract the id from the m2o tuple (id, name)
        for field in self.M2O_DYNAMIC_FIELDS:
            if isinstance(vals[field], tuple):
                vals[field] = vals[field][0]

        vals['max_comparison'] = self.COMPARISON_LEVEL
        data['form'].update(vals)
        return data
