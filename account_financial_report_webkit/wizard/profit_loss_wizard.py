# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011 Camptocamp SA (http://www.camptocamp.com)
#
# Author : Guewen Baconnier (Camptocamp)
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

from lxml import etree
from tools.translate import _
from osv import fields, osv

LEVEL_STYLES = 6

DEFAULT_STYLES = {
    'print': [True, True, True, True, True, True],
    'size': [12, 11, 10, 9, 9, 9],
    'bold': [True, True, True, False, False, False],
    'italic': [False, False, False, False, False, False],
    'underline': [False, False, False, False, False, False],
    'uppercase': [True, True, False, False, False, False],
}

class AccountProfitAndLossLedgerWizard(osv.osv_memory):
    """Will launch trial balance report and pass required args"""

    _inherit = "account.common.balance.report"
    _name = "profit.loss.webkit"
    _description = "Profit and Loss Report"

    _columns = {
        'numbers_display': fields.selection([('normal', 'Normal'), ('round', 'Round (No decimal)'), ('kilo', 'Kilo')], 'Numbers Display', required=True)
    }

    _defaults = {
        'numbers_display': 'normal',
    }

    def view_init(self, cr, uid, fields_list, context=None):
        """
         Creates view dynamically and adding fields at runtime.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: New arch of view with new columns.
        """
        res = super(AccountProfitAndLossLedgerWizard, self).view_init(cr, uid, fields_list, context=context)
        for index in range(LEVEL_STYLES):
            # create columns for each comparison page
            self._columns.update({
                "level%s_print" % (index,):
                    fields.boolean('Print'),
                "level%s_size" % (index,):
                    fields.integer('Size', required=True),
                "level%s_bold" % (index,):
                    fields.boolean('Bold'),
                "level%s_italic" % (index,):
                    fields.boolean('Italic'),
                "level%s_underline" % (index,):
                    fields.boolean('Underline'),
                "level%s_uppercase" % (index,):
                    fields.boolean('Uppercase'),
            })
        return res

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
        res = super(AccountProfitAndLossLedgerWizard, self).default_get(cr, uid, fields, context=context)

        for key, values in DEFAULT_STYLES.iteritems():
            for index in range(LEVEL_STYLES):
                field = "level%s_%s" % (index, key)
                if not res.get(field, False):
                    res[field] = values[index]
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(AccountProfitAndLossLedgerWizard, self).fields_view_get(cr, uid, view_id, view_type, context=context, toolbar=toolbar, submenu=submenu)

        eview = etree.fromstring(res['arch'])
        placeholder = eview.xpath("//group[@name='levels']")
        if placeholder:
            placeholder = placeholder[0]
            for index in range(LEVEL_STYLES):
                # add fields
                res['fields']["level%s_print" % (index,)] = {'string': "Print", 'type': 'boolean'}
                res['fields']["level%s_size" % (index,)] = {'string': "Size", 'type': 'integer', 'required': True}
                res['fields']["level%s_bold" % (index,)] = {'string': "Bold", 'type': 'boolean',}
                res['fields']["level%s_italic" % (index,)] = {'string': "Italic", 'type': 'boolean',}
                res['fields']["level%s_underline" % (index,)] = {'string': "Underline", 'type': 'boolean',}
                res['fields']["level%s_uppercase" % (index,)] = {'string': "Uppercase", 'type': 'boolean'}

                common_attrs = "{'readonly': [('level%(index)s_print', '=', False)]}" % {'index': index}
                group = etree.Element('group', {'name': "group_level_%s" % (index,), 'colspan':'4', 'col': '10'})
                group.append(etree.Element('separator', {'string': _('Level %s') % (index+1,), 'colspan':'2'}))
                group.append(etree.Element('field', {'name': "level%s_print" % (index,), 'colspan': '8'}))
                group.append(etree.Element('field', {'name': "level%s_size" % (index,), 'attrs': common_attrs}))
                group.append(etree.Element('field', {'name': "level%s_bold" % (index,), 'attrs': common_attrs}))
                group.append(etree.Element('field', {'name': "level%s_italic" % (index,), 'attrs': common_attrs}))
                group.append(etree.Element('field', {'name': "level%s_underline" % (index,), 'attrs': common_attrs}))
                group.append(etree.Element('field', {'name': "level%s_uppercase" % (index,), 'attrs': common_attrs}))

                placeholder.append(group)
        res['arch'] = etree.tostring(eview)
        return res

    def _print_report(self, cursor, uid, ids, data, context=None):
        context = context or {}
        # we update form with display account value
        data = self.pre_print_report(cursor, uid, ids, data, context=context)

        fields_to_read = ['numbers_display',]

        # comparison fields
        for index in range(LEVEL_STYLES):
            fields_to_read.extend([
                "level%s_print" % (index,),
                "level%s_size" % (index,),
                "level%s_bold" % (index,),
                "level%s_italic" % (index,),
                "level%s_underline" % (index,),
                "level%s_uppercase" % (index,),
            ])

        vals = self.read(cursor, uid, ids, fields_to_read,context=context)[0]

        data['form'].update(vals)
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.account_report_profit_loss_webkit',
                'datas': data}

AccountProfitAndLossLedgerWizard()
