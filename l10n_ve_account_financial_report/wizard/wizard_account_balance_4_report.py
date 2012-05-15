# -*- encoding: utf-8 -*-
from osv import osv,fields
from tools.translate import _
import pooler
import time

class wizard_reporte_comprobacion(osv.osv_memory):
    _name = "wizard.reporte.comprobacion"
    
    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'account_list': fields.many2many ('account.account', 'rel_wizard_account', 'account_list', 'account_id', 'Cuentas Contables', required=True),
        'filter': fields.selection([('bydate','By Date'), ('byperiod','By Period'), ('all','By Date and Period'), ('none','No Filter')], 'Date/Period Filter'),
        'fiscalyear': fields.many2one('account.fiscalyear', 'Fiscal year', help='Keep empty to use all open fiscal years to compute the balance', required=True),
        'periods': fields.many2many('account.period', 'rel_wizard_period', 'wizard_id', 'period_id', 'Periods', help='All periods in the fiscal year if empty'),
        'display_account': fields.selection([('all','All'), ('con_balance', 'With balance'),('con_movimiento', 'With movements')], 'Display accounts'),
        'display_account_level': fields.integer('Up to level', help='Display accounts up to this level (0 to show all)'),
        'date_from': fields.date('Start date'),
        'date_to': fields.date('End date'),
        'tot_check': fields.boolean('Show Total'),
        'lab_str': fields.char('Description', size= 128),
        'inf_type': fields.selection([('bml', 'Mayor Analitico')], 'Tipo Informe', required=True),
        'asentado': fields.selection([('posted', 'Todos los asientos asentados'), ('todo', 'Todos los asientos')], 'Movimientos destino', required=True),
        'analytic_list': fields.many2many('account.analytic.account', 'rel_wizard_account_analytic', 'analytic_list', 'account_analytic_id', 'Cuentas Analiticas'),
    }
    
    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-%m-%d'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
        'filter': lambda *a:'byperiod',
        'display_account_level': lambda *a: 0,
        'inf_type': lambda *a:'bml',
        'company_id': lambda *a: 1,
        'fiscalyear': lambda self, cr, uid, c: self.pool.get('account.fiscalyear').find(cr, uid),
        'display_account': lambda *a:'con_movimiento',
        'asentado': lambda *a:'todo',
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
    
    def esta_en_lista(self, cuenta_id, lista_cuentas):
        for i in lista_cuentas:
            if cuenta_id == i:
                return True
        return False
    
    def limpiar_hijos(self, cr, uid, ids, data):
        accounts = []
        accounts = data
        aa_obj = self.pool.get("account.account")
        new_account_list = []
        for aa_brw in aa_obj.browse(cr,uid,accounts):
            eliminar = False
            parent_id_cur = aa_brw.parent_id
            while parent_id_cur:
                if self.esta_en_lista(parent_id_cur.id, accounts):
                    parent_id_cur = False
                    eliminar = True
                else:
                    parent_id_cur = parent_id_cur.parent_id
            if not eliminar:
                new_account_list.append(aa_brw.id)
        return new_account_list
    
    def todos_periodos(self, cr, uid, fiscalyear):
        date = self.pool.get('account.fiscalyear').read(cr, uid, fiscalyear, ['date_start','date_stop'])
        return date['date_start'],date['date_stop']
        
    def get_cuentas_analiticas(self, cr, uid, lista_analitica):
        if lista_analitica != []:
            return lista_analitica
        else:
            return self.pool.get('account.analytic.account').search(cr, uid, [('type','<>','view')])
    
    def print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
            
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids[0])

        if data['form']['filter'] == 'byperiod':
            if data['form']['periods'] == []:
                raise osv.except_osv(_('Error !'),('Debe agregar al menos un periodo'))
            del data['form']['date_from']
            del data['form']['date_to']
        elif data['form']['filter'] == 'bydate':
            self._check_date(cr, uid, data)
            del data['form']['periods']
        elif data['form']['filter'] == 'none':
            del data['form']['periods']
            data['form']['date_from'],data['form']['date_to'] = self.todos_periodos(cr,uid,data['form']['fiscalyear'])
        else:
            if data['form']['periods'] == []:
                raise osv.except_osv(_('Error !'),('Debe agregar al menos un periodo'))
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
        
        if data.has_key('form') and data['form']:
            form = data['form']
            if form.has_key('account_list') and form['account_list']:
                form['account_list'] = self.limpiar_hijos(cr, uid, ids, form['account_list'])
        
        if str(data['form']['asentado']).strip() == 'posted':
            data['form']['state'] = 'posted'
        del data['form']['asentado']
        
        if data['form']['inf_type'] == 'bml':
            data['form']['tot_check'] = False
            data['form']['display_account_level'] = 0
            data['form']['display_account'] = 'con_movimiento'
            return {'type': 'ir.actions.report.xml', 'report_name': 'wizard.reporte.comprobacion.mayor.analitico', 'datas': data}
        elif data['form']['inf_type'] == 'bac':
            data['form']['tot_check'] = False
            data['form']['display_account_level'] = 0
            data['form']['display_account'] = 'con_movimiento'
            data['form']['analytic_list'] = self.get_cuentas_analiticas(cr, uid,data['form']['analytic_list'])
            return {'type': 'ir.actions.report.xml', 'report_name': 'wizard.reporte.comprobacion.analisis.cuentas', 'datas': data}
        elif data['form']['inf_type'] == 'bgen':
            return {'type': 'ir.actions.report.xml', 'report_name': 'wizard.reporte.comprobacion.un.col', 'datas': data}
        else:
            return {'type': 'ir.actions.report.xml', 'report_name': 'wizard.reporte.comprobacion.cuatro.col', 'datas': data}
            
wizard_reporte_comprobacion()
