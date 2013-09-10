# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Joel Grand-Guillaume and Vincent Renaville Copyright 2013 Camptocamp SA
#    CSV data formating inspired from http://docs.python.org/2.7/library/csv.html?highlight=csv#examples
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

import time
import StringIO
import cStringIO
import base64

import csv
import codecs

from openerp.osv import orm, fields
from openerp.tools.translate import _


class AccountUnicodeWriter(object):
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        # created a writer with Excel formating settings
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        #we ensure that we do not try to encode none or bool
        row = [x or u'' for x in row]

        encoded_row = []
        for c in row:
            if type(c) == unicode:
                encoded_row.append(c.encode("utf-8"))
            else:
                encoded_row.append(c)

        self.writer.writerow(encoded_row)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

class AccountCSVExport(orm.TransientModel):
    _name = 'account.csv.export'
    _description = 'Export Accounting'

    _columns = {
        'data': fields.binary('CSV',readonly=True),
        'company_id': fields.many2one('res.company', 'Company', invisible=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscalyear', required=True),
        'periods': fields.many2many('account.period','rel_wizard_period','wizard_id','period_id','Periods',help='All periods in the fiscal year if empty'),
        'export_filename': fields.char('Export CSV Filename', size=128),
    }

    def _get_company_default(self, cr, uid, context=None):
        comp_obj = self.pool['res.company']
        return comp_obj._company_default_get(cr, uid, 'account.fiscalyear', context=context)

    def _get_fiscalyear_default(self, cr, uid, context=None):
        fiscalyear_obj = self.pool['account.fiscalyear']
        context['company_id'] = self._get_company_default(cr, uid, context)
        return fiscalyear_obj.find(cr,uid,dt=None,exception=True, context=context)

    _defaults = {'company_id': _get_company_default,
                 'fiscalyear_id' : _get_fiscalyear_default,
                 'export_filename' : 'account_export.csv'}

    def action_manual_export_account(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        rows = self.get_data(cr, uid, ids,"account", context)
        file_data = StringIO.StringIO()
        try:
            writer = AccountUnicodeWriter(file_data)
            writer.writerows(rows)
            file_value = file_data.getvalue()
            self.write(cr, uid, ids,
                       {'data': base64.encodestring(file_value)},
                       context=context)
        finally:
            file_data.close()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.csv.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }


    def _get_header_account(self, cr, uid, ids, context=None):
        return [_(u'CODE'),
                _(u'NAME'),
                _(u'DEBIT'),
                _(u'CREDIT'),
                _(u'BALANCE'),
                ]

    def _get_rows_account(self, cr, uid, ids, fiscalyear_id,period_range_ids,company_id,context=None):
        """
        Return list to generate rows of the CSV file
        """
        cr.execute("""
                        select ac.code,ac.name,
                        sum(debit) as sum_debit,sum(credit) as sum_credit,sum(debit) - sum(credit) as balance
                        from account_move_line as aml,account_account as ac
                        where aml.account_id = ac.id
                        and period_id in %(period_ids)s
                        group by ac.id,ac.code,ac.name
                        order by ac.code
                   """,
                    {'fiscalyear_id': fiscalyear_id,'company_id':company_id,'period_ids':tuple(period_range_ids)}
                )
        res = cr.fetchall()

        rows = []
        for line in res:
            rows.append(list(line))
        return rows

    def action_manual_export_analytic(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        rows = self.get_data(cr, uid, ids,"analytic", context)
        file_data = StringIO.StringIO()
        try:
            writer = AccountUnicodeWriter(file_data)
            writer.writerows(rows)
            file_value = file_data.getvalue()
            self.write(cr, uid, ids,
                       {'data': base64.encodestring(file_value)},
                       context=context)
        finally:
            file_data.close()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.csv.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _get_header_analytic(self, cr, uid, ids, context=None):
        return [_(u'ANALYTIC CODE'),
                _(u'ANALYTIC NAME'),
                _(u'CODE'),
                _(u'ACCOUNT NAME'),
                _(u'DEBIT'),
                _(u'CREDIT'),
                _(u'BALANCE'),
                ]

    def _get_rows_analytic(self, cr, uid, ids, fiscalyear_id,period_range_ids,company_id,context=None):
        """
        Return list to generate rows of the CSV file
        """
        cr.execute("""  select aac.code as analytic_code,aac.name as analytic_name,ac.code,ac.name,
                        sum(debit) as sum_debit,sum(credit) as sum_credit,sum(debit) - sum(credit) as balance
                        from account_move_line 
                        left outer join account_analytic_account as aac
                        on (account_move_line.analytic_account_id = aac.id)
                        inner join account_account as ac
                        on account_move_line.account_id = ac.id
                        and account_move_line.period_id in %(period_ids)s
                        group by aac.id,aac.code,aac.name,ac.id,ac.code,ac.name
                        order by aac.code
                   """,
                    {'fiscalyear_id': fiscalyear_id,'company_id':company_id,'period_ids':tuple(period_range_ids)}
                )
        res = cr.fetchall()

        rows = []
        for line in res:
            rows.append(list(line))
        return rows

    def get_data(self, cr, uid, ids,result_type,context=None):
        get_header_func = getattr(self,("_get_header_%s"%(result_type)), None)
        get_rows_func = getattr(self,("_get_rows_%s"%(result_type)), None)
        form = self.browse(cr, uid, ids[0], context=context)
        fiscalyear_id = form.fiscalyear_id.id
        user_obj = self.pool.get('res.users')
        company_id = user_obj.browse(cr, uid, uid).company_id.id
        if form.periods:
            period_range_ids = [x.id for x in form.periods]
        else:
            # If not period selected , we take all periods
            p_obj = self.pool.get("account.period")
            period_range_ids = p_obj.search(cr,uid,[('fiscalyear_id','=',fiscalyear_id)],context=context)
        rows = []
        rows.append(get_header_func(cr, uid, ids, context=context))
        rows.extend(get_rows_func(cr, uid, ids, fiscalyear_id,period_range_ids,company_id, context=context))
        return rows
