# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Joel Grand-Guillaume and Vincent Renaville Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
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


class AccountUnicodeWriter(object):
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        # self.writer = csv.writer(self.queue, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC, **kwds)
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
        # self.writer.writerow([s.encode("utf-8") for s in row])
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


# TODO / Improve: Choose a fiscal year !
class AccountCSVExport(orm.TransientModel):
    _name = 'account.csv.export'
    _description = 'Export Accounting Entries'

    _columns = {
        'data': fields.binary('CSV',readonly=True),
        'company_id': fields.many2one('res.company', 'Company', invisible=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscalyear', required=True),
        'start_period_id': fields.many2one('account.period', 'Starting period', required=True),
        'stop_period_id': fields.many2one('account.period', 'End period', required=True),
    }

    def _get_company_default(self, cr, uid, context=None):
        comp_obj = self.pool['res.company']
        fiscalyear_obj = self.pool['account.fiscalyear']
        return comp_obj._company_default_get(cr, uid, 'account.fiscalyear', context=context)


    _defaults = {'company_id': _get_company_default}


    def action_manual_export(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        rows = self.get_data(cr, uid, ids, context)
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


    def _get_header(self, cr, uid, ids, context=None):
        return [u'account_id',
                u'code',
                u'name'
                u'si',
                u'sum_debit',
                u'sum_credit',
                u'balance',
                ]

    def _get_rows(self, cr, uid, ids, fiscalyear_id,period_range_ids,company_id,context=None):
        """
        Return list to generate rows of the CSV file
        """
        cr.execute("""
                        select ac.id,ac.code,ac.name,
                        sum(debit) as sum_debit,sum(credit) as sum_credit,sum(debit) - sum(credit) as balance
                        from account_move_line as aml,account_account as ac
                        where aml.account_id = ac.id
                        and period_id in %(period_ids)s
                        group by ac.id,ac.code
                        order by ac.code
                   """,
                    {'fiscalyear_id': fiscalyear_id,'company_id':company_id,'period_ids':tuple(period_range_ids)}
                )
        res = cr.fetchall()
        
        rows = []
        for line in res:
            rows.append(list(line))
        return rows
    
    def get_period_range(self,cr,uid,start_period_id,stop_period_id,company_id,context=None):
        context = context or {}
        ## Get period for this company_id
        period_obj = self.pool.get('account.period')
        date_start = period_obj.browse(cr,uid,start_period_id).date_start
        date_stop = period_obj.browse(cr,uid,stop_period_id).date_stop
        start_period_ids = period_obj.search(cr, uid,
            [('date_start', '>=', date_start),
             ('company_id', '=', company_id)]
            )
        stop_period_ids = period_obj.search(cr, uid,
            [('date_stop', '<=', date_stop),
             ('company_id', '=', company_id)]
            )
        ## Get only period present in start_period_ids and stop_period_ids
        matching_period = list(set(start_period_ids).intersection(set(stop_period_ids)))
        return matching_period
    
    def get_data(self, cr, uid, ids, context=None):
        context = context or {}
        context['lang'] = 'fr_FR'

        form = self.browse(cr, uid, ids[0], context=context)

        start_period_id = form.start_period_id.id
        stop_period_id = form.stop_period_id.id
        fiscalyear_id = form.fiscalyear_id.id
        user_obj = self.pool.get('res.users')
        company_id = user_obj.browse(cr, uid, uid).company_id.id
        period_range_ids = self.get_period_range(cr, uid, start_period_id, stop_period_id,company_id,context)
        rows = []
        rows.append(self._get_header(cr, uid, ids, context=context))
        rows.extend(self._get_rows(cr, uid, ids, fiscalyear_id,period_range_ids,company_id, context=context))
        return rows


    def action_manual_export_analytic(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        rows = self.get_data_analytic(cr, uid, ids, context)
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
        return [u'account_id',
                u'analytic_account_id',
                u'code',
                u'name',
                u'analytic_code',
                u'analytic_name',
                u'sum_debit',
                u'sum_credit',
                u'balance',
                ]




    def _get_rows_analytic(self, cr, uid, ids, fiscalyear_id,period_range_ids,company_id,context=None):
        """
        Return list to generate rows of the CSV file
        """
        cr.execute("""
                        select ac.id,ac.code,ac.name,aac.id,aac.code as analytic_code,aac.name as analytic_name,
                        sum(debit) as sum_debit,sum(credit) as sum_credit,sum(debit) - sum(credit) as balance
                        from account_move_line as aml,account_account as ac,account_analytic_account as aac
                        where aml.account_id = ac.id
                        and aml.analytic_account_id = aac.id
                        and period_id in %(period_ids)s
                        group by ac.id,ac.code,aac.id,aac.code
                        order by ac.code
                   """,
                    {'fiscalyear_id': fiscalyear_id,'company_id':company_id,'period_ids':tuple(period_range_ids)}
                )
        res = cr.fetchall()
        
        rows = []
        for line in res:
            rows.append(list(line))
        return rows


    def get_data_analytic(self, cr, uid, ids, context=None):
        context = context or {}
        context['lang'] = 'fr_FR'

        form = self.browse(cr, uid, ids[0], context=context)

        start_period_id = form.start_period_id.id
        stop_period_id = form.stop_period_id.id
        fiscalyear_id = form.fiscalyear_id.id
        user_obj = self.pool.get('res.users')
        company_id = user_obj.browse(cr, uid, uid).company_id.id
        period_range_ids = self.get_period_range(cr, uid, start_period_id, stop_period_id,company_id,context)
        rows = []
        rows.append(self._get_header_analytic(cr, uid, ids, context=context))
        rows.extend(self._get_rows_analytic(cr, uid, ids, fiscalyear_id,period_range_ids,company_id, context=context))
        return rows
