# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
###############Credits######################################################
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


class account_analisis_cuentas(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(account_analisis_cuentas, self).__init__(cr, uid, name, context)
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
            'set_fecha': self.set_fecha,
        })
        self.context = context
    
    def set_fecha(self, fecha):
        f = fecha.split('-')
        date = datetime.date(int(f[0]),int(f[1]),int(f[2]))
        return str(date.strftime("%d/%m/%Y"))

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
            'edogp': 'Estado de Ganancias y Perdidas',
            'bac':   '           Analisis de Cuentas',
            'bml':   '               Mayor Analitico'
        }
        return inf_type[form['inf_type']]

    def get_periods_and_date_text(self, form):
        """
        Returns the text with the periods/dates used on the report.
        """
        period_obj = self.pool.get('account.period')
        periods_str = None
        fiscalyear_id = form['fiscalyear'] or fiscalyear_obj.find(self.cr, self.uid)
        period_ids = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear_id), ('special','=',False)])
        if form['filter'] in ['byperiod', 'all']:
            period_ids = form['periods']
            periods_str = ', '.join([period.name or period.code for period in period_obj.browse(self.cr, self.uid, period_ids)])

        dates_str = None
        if form['filter'] in ['bydate', 'all']:
            dates_str = self.formatLang(form['date_from'], date=True) + ' - ' + self.formatLang(form['date_to'], date=True) + ' '
        return {'periods':periods_str, 'date':dates_str}

    def es_especial(self, periods):
        period_obj = self.pool.get('account.period')
        period_brws = period_obj.browse(self.cr, self.uid, periods)
        tod=0
        for p_b in period_brws:
            if p_b.special:
                tod = tod + 1
        if tod == len(periods):
            return True
        else:
            return False
    
    def calcular_debito_credito(self, account, form):
        res = {}
        if form['filter'] in ('bydate','none'):
            #Para filtrar por 'fechas' o 'sin filtro', este porque se envia el año fiscal por fecha.
            where = """ and aml.date between '%s' and '%s'"""%(form['date_from'],form['date_to'])
        elif form['filter'] == 'byperiod':
            #Para filtrar por periodos
            periodos = str(form['periods']).replace("[","(").replace("]",")")
            where = """ and aml.period_id in %s"""%(periodos)
        else:
            #Para filtrar por periodos y fechas
            periodos = str(form['periods']).replace("[","(").replace("]",")")
            where = """ and aml.period_id in %s and aml.date between '%s' and '%s'"""%(periodos,form['date_from'],form['date_to'])
        if form.get('state'):
            estado = " and am.state = '%s'"%form['state']
            where = where + estado
        
        analytic_list = str(form['analytic_list']).replace("[","(").replace("]",")")
        where = where + " and aaa.id in " + analytic_list
        
        account_list = str(account).replace("[","(").replace("]",")")
        where = where + " and aa.id in " + account_list
        
        sql_saldos = """select 	aml.account_id as id,
            COALESCE(SUM(aml.debit), 0) as debit, 
            COALESCE(SUM(aml.credit), 0) as credit
            from account_move_line aml
            inner join account_analytic_account aaa on aml.analytic_account_id = aaa.id
            inner join account_journal aj on aj.id = aml.journal_id
            inner join account_account aa on aa.id = aml.account_id
            inner join account_period ap on ap.id = aml.period_id
            inner join account_move am on am.id = aml.move_id
            where aml.state <> 'draft'""" + where + \
            """ group by aml.account_id"""
            
        self.cr.execute(sql_saldos)
        resultat = self.cr.dictfetchall()

        for det in resultat:
            res[det['id']] = {
                'debit': det['debit'],
                'credit': det['credit'],
            }
        return res
    
    def _get_analisis_cuenta_analitica(self, account, form):
        res = []
        if form['filter'] in ('bydate','none'):
            #Para filtrar por 'fechas' o 'sin filtro', este porque se envia el año fiscal por fecha.
            where = """ and aml.date between '%s' and '%s'"""%(form['date_from'],form['date_to'])
        elif form['filter'] == 'byperiod':
            #Para filtrar por periodos
            periodos = str(form['periods']).replace("[","(").replace("]",")")
            where = """ and aml.period_id in %s"""%(periodos)
        else:
            #Para filtrar por periodos y fechas
            periodos = str(form['periods']).replace("[","(").replace("]",")")
            where = """ and aml.period_id in %s and aml.date between '%s' and '%s'"""%(periodos,form['date_from'],form['date_to'])
        if form.get('state'):
            estado = " and am.state = '%s'"%form['state']
            where = where + estado
        
        where = where + " and aa.id = '%s'"%(account['id'])
        analytic_list = str(form['analytic_list']).replace("[","(").replace("]",")")
        where = where + " and aaa.id in " + analytic_list
        
        sql_detalle = """select aml.id as id, aj.name as diario,
            aa.name as descripcion,
            (select name from res_partner where aml.partner_id = id) as partner,
            aa.code as cuenta, aml.name || ' -- Ref: ' || aml.ref as ref,
            case when aml.debit is null then 0.00 else aml.debit end as debit, 
            case when aml.credit is null then 0.00 else aml.credit end as credit,
            aml.date as fecha, ap.name as periodo,
            aaa.code as analitica
            from account_move_line aml
            inner join account_analytic_account aaa on aml.analytic_account_id = aaa.id
            inner join account_journal aj on aj.id = aml.journal_id
            inner join account_account aa on aa.id = aml.account_id
            inner join account_period ap on ap.id = aml.period_id
            inner join account_move am on am.id = aml.move_id
            where aml.state <> 'draft'""" + where + \
            """ order by analitica, fecha"""
            
        self.cr.execute(sql_detalle)
        resultat = self.cr.dictfetchall()
        balance = account['balanceinit']
        
        for det in resultat:
            balance += det['debit'] - det['credit']
            res.append({
                'id': det['id'],
                'date': det['fecha'],
                'journal':det['diario'],
                'ref': det['ref'],
                'debit': det['debit'],
                'credit': det['credit'],
                'analytic': det['analitica'],
                'period': det['periodo'],
                'balance': balance,
            })
        return res
    
    def lines(self, form, ids={}, done=None, level=0):
        """
        Returns all the data needed for the report lines
        (account info plus debit/credit/balance in the selected period
        and the full year)
        """
        tot_bin = 0.0
        tot_deb = 0.0
        tot_crd = 0.0
        tot_eje = 0.0
        if not ids:
            ids = self.ids
        if not ids:
            return []
        if not done:
            done = {}
    
        if form.has_key('account_list') and form['account_list']:
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
        
        account_obj = self.pool.get('account.account')
        period_obj = self.pool.get('account.period')
        fiscalyear_obj = self.pool.get('account.fiscalyear')

        #############################################################################
        # Calculate the period Debit/Credit                                         #
        # (from the selected period or all the non special periods in the fy)       #
        #############################################################################
        ctx = self.context.copy()
        ctx['filter'] = form.get('filter','all')
        ctx['fiscalyear'] = fiscalyear.id
        if ctx['filter'] not in ['bydate','none']:
            especial = self.es_especial(form['periods'])
        else:
            especial = False
        if form['filter'] in ['byperiod', 'all']:
            if especial:
                ctx['periods'] = period_obj.search(self.cr, self.uid, [('id','in',form['periods'] or ctx['periods'])])
            else:
                ctx['periods'] = period_obj.search(self.cr, self.uid, [('id','in',form['periods'] or ctx['periods']), ('special','=',False)])
        
        if form['filter'] in ['bydate','all','none']:
            ctx['date_from'] = form['date_from']
            ctx['date_to'] = form['date_to']
        
        accounts=[]
        
        val = account_obj.browse(self.cr, self.uid, [aa_id[0] for aa_id in account_ids], ctx)
        
        """DESDE AQUI VOY A COMENZAR A CAMBIAR"""
        #Extraer cuentas que no son tipo vista
        cuenta_ids = {}
        for cue in val:
            if cue.type != 'view':
                cuenta_ids[cue.id] = cue
        account_ids = self.calcular_debito_credito(cuenta_ids.keys(), form)
        
        if account_ids != {}:
            for acc in account_ids.keys():
                new_acc = {
                    'id'        :acc,
                    'type'      :cuenta_ids[acc].type,
                    'code'      :str(cuenta_ids[acc].code),
                    'name'      :cuenta_ids[acc].name.upper(),
                    'parent_id' :cuenta_ids[acc].parent_id and cuenta_ids[acc].parent_id.id,
                    'level'     :cuenta_ids[acc].level,
                    'label'     :True,
                    'total'     :True,
                    'debit'     :account_ids[acc]['debit'],
                    'credit'    :account_ids[acc]['credit'],
                }
                accounts.append(new_acc)
        
        def missing_period():
            ctx['fiscalyear'] = fiscalyear_obj.search(self.cr, self.uid, [('date_stop','<',fiscalyear.date_start)],order='date_stop') and \
                                fiscalyear_obj.search(self.cr, self.uid, [('date_stop','<',fiscalyear.date_start)],order='date_stop')[-1] or []
            ctx['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',ctx['fiscalyear']),('date_stop','<',fiscalyear.date_start)])
        
        #############################################################################
        # Calculate the period initial Balance                                      #
        # (fy balance minus the balance from the start of the selected period       #
        #  to the end of the year)                                                  #
        #############################################################################
        
        ctx = self.context.copy()
        if form.get('state'):
            ctx['state'] = form['state']
        
        if form.get('analytic_list'):
            ctx['analytic_list'] = form['analytic_list']
        
        ctx['filter'] = form.get('filter','all')
        ctx['fiscalyear'] = fiscalyear.id
        
        if form['filter'] in ['byperiod']:
            ctx['periods'] = form['periods']
            date_start = min([period.date_start for period in period_obj.browse(self.cr, self.uid, ctx['periods'])])
            ctx['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('date_stop','<=',date_start)])
            if not ctx['periods']:
                missing_period()
        elif form['filter'] in ['bydate', 'all']:
            ctx['date_from'] = fiscalyear.date_start
            ctx['date_to'] = form['date_from']
            ctx['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('date_stop','<=',ctx['date_to'])])
        elif form['filter'] == 'none':
            ctx['date_from'] = form['date_from']
            ctx['date_to'] = form['date_to']
            ctx['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('special','=',True)])
            date_start = min([period.date_start for period in period_obj.browse(self.cr, self.uid, ctx['periods'])])
            ctx['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('date_start','<=',date_start),('special','=',True)])
        
        for acc in accounts:
            if especial:
                acc['balanceinit'] = 0.0
                acc['balance'] = acc['debit'] - acc['credit']
            else:
                account_ids_ant = self.calcular_debito_credito([acc['id']], ctx)
                if account_ids_ant != {}:
                    acc['balanceinit'] = account_ids_ant[acc['id']]['debit'] - account_ids_ant[acc['id']]['credit']
                    acc['balance'] = acc['balanceinit'] + acc['debit'] - acc['credit']
                else:
                    acc['balanceinit'] = 0.0
                    acc['balance'] = acc['debit'] - acc['credit']
        
        for acc_anl in accounts:
            acc_anl['analisis'] = self._get_analisis_cuenta_analitica(acc_anl,form)
        accounts.sort(key=lambda x: x['code'])
        
        return accounts

report_sxw.report_sxw('report.wizard.reporte.comprobacion.analisis.cuentas', 'wizard.reporte.comprobacion', 'l10n_ve_account_financial_report/report/analisis_cuentas.rml', parser=account_analisis_cuentas, header=False)
