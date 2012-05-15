# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
###############Credits######################################################
#    Coded by:   Humberto Arocha humberto@openerp.com.ve
#                Angelica Barrios angelicaisabelb@gmail.com
#               Jordi Esteve <jesteve@zikzakmedia.com>
#               Javier Duran <javieredm@gmail.com>
#    Planified by: Humberto Arocha
#    Finance by: LUBCAN COL S.A.S http://www.lubcancol.com
#    Audited by: Humberto Arocha humberto@openerp.com.ve
#############################################################################
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
##############################################################################

import xml
import copy
from operator import itemgetter
import time
import datetime
from report import report_sxw
from tools import config


class account_balance(report_sxw.rml_parse):


    def __init__(self, cr, uid, name, context):
        print 'INICIO: ',datetime.datetime.now()
        super(account_balance, self).__init__(cr, uid, name, context)
        self.sum_debit = 0.00
        self.sum_credit = 0.00
        self.sum_balance = 0.00
        self.sum_debit_fy = 0.00
        self.sum_credit_fy = 0.00
        self.sum_balance_fy = 0.00
        self.date_lst = []
        self.date_lst_string = ''
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'get_fiscalyear_text': self.get_fiscalyear_text,
            'get_periods_and_date_text': self.get_periods_and_date_text,
            'get_inf_text': self.get_informe_text,            
        })
        self.context = context


    def get_fiscalyear_text(self, form):
        """
        Returns the fiscal year text used on the report.
        """
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        fiscalyear = None
        if form.get('fiscalyear'):
            fiscalyear = fiscalyear_obj.browse(self.cr, self.uid, form['fiscalyear'])
            return fiscalyear.name or fiscalyear.code
        else:
            fiscalyear = fiscalyear_obj.browse(self.cr, self.uid, fiscalyear_obj.find(self.cr, self.uid))
            return "%s*" % (fiscalyear.name or fiscalyear.code)

    def get_informe_text(self, form):
        """
        Returns the header text used on the report.
        """
        inf_type = {
            'bgen' : '               Balance General',
            'bcom' : '       Balance de Comprobacion',            
            'edogp': 'Estado de Ganancias y Perdidas' 
        }
        return inf_type[form['inf_type']]

    def get_periods_and_date_text(self, form):
        """
        Returns the text with the periods/dates used on the report.
        """
        period_obj = self.pool.get('account.period')
        periods_str = None
        fiscalyear_id = form['fiscalyear'] or fiscalyear_obj.find(self.cr, self.uid)
        period_ids = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear_id),('special','=',False)])
        if form['filter'] in ['byperiod', 'all']:
            period_ids = form['periods']
            periods_str = ', '.join([period.name or period.code for period in period_obj.browse(self.cr, self.uid, period_ids)])

        dates_str = None
        if form['filter'] in ['bydate', 'all']:
            dates_str = self.formatLang(form['date_from'], date=True) + ' - ' + self.formatLang(form['date_to'], date=True) + ' '

        return {'periods':periods_str, 'date':dates_str}


    def lines(self, form, ids={}, done=None, level=0):
        """
        Returns all the data needed for the report lines
        (account info plus debit/credit/balance in the selected period
        and the full year)
        """
        tot_deb = 0.0
        tot_crd = 0.0
        if not ids:
            ids = self.ids
        if not ids:
            return []
        if not done:
            done = {}
        print "Lista Form %s"%form
        print "Tipo de Obj %s"%type(form)

        print "form:%s"%form
        if form.has_key('account_list') and form['account_list']:
            #account_ids = form['account_list'][0][2]
            account_ids = form['account_list']
            del form['account_list']
        res = {}
        result_acc = []
        accounts_levels = {}
        account_obj = self.pool.get('account.account')
        period_obj = self.pool.get('account.period')
        fiscalyear_obj = self.pool.get('account.fiscalyear')

        # Get the fiscal year
        fiscalyear = None
        if form.get('fiscalyear'):
            fiscalyear = fiscalyear_obj.browse(self.cr, self.uid, form['fiscalyear'])
        else:
            fiscalyear = fiscalyear_obj.browse(self.cr, self.uid, fiscalyear_obj.find(self.cr, self.uid))

        #
        # Get the accounts
        #
        def _get_children_and_consol(cr, uid, ids, level, context={}):
            aa_obj = self.pool.get('account.account')
            ids2=[]
            temp=[]
            read_data= aa_obj.read(cr, uid, ids,['id','child_id','level','type'], context)
            for data in read_data:
                if data['child_id'] and data['level'] < level and data['type']!='consolidation':
                    #ids2.append([data['id'],'Label', 'Total'])
                    ids2.append([data['id'],True, False])
                    temp=[]
                    for x in data['child_id']:
                        temp.append(x)
                    ids2 += _get_children_and_consol(cr, uid, temp, level, context)
                    ids2.append([data['id'],False,True])
                else:
                    ids2.append([data['id'],True,True])
            return ids2

        child_ids = _get_children_and_consol(self.cr, self.uid, account_ids, form['display_account_level'] and form['display_account_level'] or 100,self.context)
        if child_ids:
            account_ids = child_ids

        #
        # Calculate the period Debit/Credit
        # (from the selected period or all the non special periods in the fy)
        #
        ctx = self.context.copy()
        print "CTX = %s\nY\nFORM = %s"%(ctx,form)
        ctx['filter'] = form.get('filter','all')
        #~ ctx['filter'] = form['context'].get('filter','all')
        ctx['fiscalyear'] = fiscalyear.id
        ctx['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('special','=',False)])
        if form['filter'] in ['byperiod', 'all']:
            print "PERIODS ",form['periods']
            #~ ctx['periods'] = form['periods'][0][2]
            ctx['periods'] = form['periods']
        if form['filter'] in ['bydate', 'all']:
            ctx['date_from'] = form['date_from']
            ctx['date_to'] = form['date_to']

        accounts=[]
        for aa_id in account_ids:
                new_acc = account_obj.read(self.cr, self.uid, aa_id[0], ['type','code','name','debit','credit','parent_id','level'], ctx)
                new_acc.update({'label':aa_id[1],'total':aa_id[2]})
                accounts.append(new_acc)
        
        def missing_period():
            ctx['fiscalyear'] = fiscalyear_obj.search(self.cr, self.uid, [('date_stop','<',fiscalyear.date_start)],order='date_stop') and \
                                fiscalyear_obj.search(self.cr, self.uid, [('date_stop','<',fiscalyear.date_start)],order='date_stop')[-1] or []
            ctx['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',ctx['fiscalyear']),('date_stop','<',fiscalyear.date_start)])
        

        #
        # Generate the report lines (checking each account)
        #
        tot = {}        
        for account in accounts:
            account_id = account['id']

            if account_id in done:
                pass
#                continue

            done[account_id] = 1

            accounts_levels[account_id] = account['level']

            #
            # Check if we need to include this level
            #
            if not form['display_account_level'] or account['level'] <= form['display_account_level']:
                #
                # Copy the account values
                #
                res = {
                        'id' : account_id,
                        'type' : account['type'],
                        'code': account['code'],
                        'name': (account['total'] and not account['label']) and 'TOTAL %s'%(account['name'].upper()) or account['name'],
                        'level': account['level'],
                        'debit': account['debit'],
                        'credit': account['credit'],
                        'parent_id': account['parent_id'],
                        'bal_type': '',
                        'label': account['label'],
                        'total': account['total'],
                    }

                #
                # Check whether we must include this line in the report or not
                #
                if form['display_account'] == 'con_movimiento' and account['parent_id']:
                    # Include accounts with movements
                    if abs(res['credit']-res['debit']) >= 0.5 * 10**-int(2) \
                                or abs(res['credit']) >= 0.5 * 10**-int(2) \
                                or abs(res['debit']) >= 0.5 * 10**-int(2):
                        result_acc.append(res)
                elif form['display_account'] == 'con_balance' and account['parent_id']:
                    # Include accounts with balance
                    if abs(res['credit']-res['debit']) >= 0.5 * 10**-int(2):
                        result_acc.append(res)
                else:
                    # Include all account
                    result_acc.append(res)
                if form['tot_check'] and res['type'] == 'view' and res['level'] == 1 and (res['id'] not in tot):
                    tot[res['id']] = True
                    tot_deb += res['debit']
                    tot_crd += res['credit']
        if form['tot_check']:
            str_label = form['lab_str']
            res2 = {
                    'type' : 'view',
                    'name': 'TOTAL %s'%(str_label),
                    'debit': tot_deb,
                    'credit': tot_crd,
                    'label': False,
                    'total': True,
            }
            result_acc.append(res2)
        print 'FIN: ',datetime.datetime.now()
        return result_acc
report_sxw.report_sxw('report.wizard.reporte.comprobacion.dos.col', 
                      'account.account', 
                      'l10n_ve_account_financial_report/report/balance_full_2_cols.rml',
                       parser=account_balance, 
                       header=False)
