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

from osv import osv,fields
import pooler
import time

class wizard_report(osv.osv_memory):
    _name = "wizard.report"

    _columns = {
        'company_id': fields.many2one('res.company','Company',required=True),
        'account_list': fields.many2many ('account.account','rel_wizard_account','account_list','account_id','Root accounts',required=True),
        'filter': fields.selection([('bydate','By Date'),('byperiod','By Period'),('all','By Date and Period'),('none','No Filter')],'Date/Period Filter'),
        'fiscalyear': fields.many2one('account.fiscalyear','Fiscal year',help='Keep empty to use all open fiscal years to compute the balance',required=True),
        'periods': fields.many2many('account.period','rel_wizard_period','wizard_id','period_id','Periods',help='All periods in the fiscal year if empty'),
        'display_account': fields.selection([('all','All'),('con_balance', 'With balance'),('con_movimiento','With movements')],'Display accounts'),
        'display_account_level': fields.integer('Up to level',help='Display accounts up to this level (0 to show all)'),
        'date_from': fields.date('Start date'),
        'date_to': fields.date('End date'),
        'tot_check': fields.boolean('Show Total'),
        'lab_str': fields.char('Description', size= 128),
        'inf_type': fields.selection([('bgen','Balance General'),('bcom','Balance Comprobacion'),('edogp','Estado Ganancias y Perdidas'),('bml','Libro Mayor Legal')],'Tipo Informe',required=True),
        #~ 'type_report': fields.selection([('un_col','Una Columna'),('dos_col','Dos Columnas'),('cuatro_col','Cuatro Columnas')],'Tipo Informe',required=True),
    }
    
    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-%m-%d'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
        'filter': lambda *a:'byperiod',
        'display_account_level': lambda *a: 0,
        'inf_type': lambda *a:'bcom',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=c),
        'fiscalyear': lambda self, cr, uid, c: self.pool.get('account.fiscalyear').find(cr, uid),
        'display_account': lambda *a:'con_movimiento',
    }
    
    def onchange_filter(self,cr,uid,ids,fiscalyear,filters,context=None):
        if context is None:
            context = {}
        res = {}
        if filters in ("bydate","all"):
            fisy = self.pool.get("account.fiscalyear")
            fis_actual = fisy.browse(cr,uid,fiscalyear,context=context)
            res = {'value':{'date_from': fis_actual.date_start, 'date_to': fis_actual.date_stop}}
        return res
    
    def _get_defaults(self, cr, uid, data, context=None):
        if context is None:
            context = {}
        user = pooler.get_pool(cr.dbname).get('res.users').browse(cr, uid, uid, context=context)
        if user.company_id:
           company_id = user.company_id.id
        else:
           company_id = pooler.get_pool(cr.dbname).get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
        data['form']['company_id'] = company_id
        fiscalyear_obj = pooler.get_pool(cr.dbname).get('account.fiscalyear')
        data['form']['fiscalyear'] = fiscalyear_obj.find(cr, uid)
        data['form']['context'] = context
        return data['form']

    def _check_state(self, cr, uid, data, context=None):
        if context is None:
            context = {}
        if data['form']['filter'] == 'bydate':
           self._check_date(cr, uid, data, context)
        return data['form']
    
    def _check_date(self, cr, uid, data, context=None):
        if context is None:
            context = {}
            
        if data['form']['date_from'] > data['form']['date_to']:
            raise osv.except_osv(_('Error !'),('La fecha final debe ser mayor a la inicial'))
        
        sql = """SELECT f.id, f.date_start, f.date_stop
            FROM account_fiscalyear f
            WHERE '%s' = f.id """%(data['form']['fiscalyear'])
        cr.execute(sql)
        res = cr.dictfetchall()

        if res:
            if (data['form']['date_to'] > res[0]['date_stop'] or data['form']['date_from'] < res[0]['date_start']):
                raise osv.except_osv(_('UserError'),'Las fechas deben estar entre %s y %s' % (res[0]['date_start'], res[0]['date_stop']))
            else:
                return 'report'
        else:
            raise osv.except_osv(_('UserError'),'No existe periodo fiscal')

    def print_report(self, cr, uid, ids,data, context=None):
        if context is None:
            context = {}
            
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids[0])

        if data['form']['filter'] == 'byperiod':
            del data['form']['date_from']
            del data['form']['date_to']
        elif data['form']['filter'] == 'bydate':
            self._check_date(cr, uid, data)
            del data['form']['periods']
        elif data['form']['filter'] == 'none':
            del data['form']['date_from']
            del data['form']['date_to']
            del data['form']['periods']
        else:
            self._check_date(cr, uid, data)
            lis2 = str(data['form']['periods']).replace("[","(").replace("]",")")
            sqlmm = """select min(p.date_start) as inicio, max(p.date_stop) as fin 
            from account_period p 
            where p.id in %s"""%lis2
            cr.execute(sqlmm)
            minmax = cr.dictfetchall()
            if minmax:
                if (data['form']['date_to'] < minmax[0]['inicio']) or (data['form']['date_from'] > minmax[0]['fin']):
                    raise osv.except_osv(_('Error !'),('La intersepcion entre el periodo y fecha es vacio'))

        return {'type': 'ir.actions.report.xml', 'report_name': 'wizard.report.reporte', 'datas': data}
            
wizard_report()
