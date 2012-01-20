# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://www.vauxoo.com>).
#    All Rights Reserved
###############Credits######################################################
#    Coded by:   Humberto Arocha humberto@openerp.com.ve
#                Angelica Barrios angelicaisabelb@gmail.com
#               Jordi Esteve <jesteve@zikzakmedia.com>
#               Javier Duran <javieredm@gmail.com>
#    Planified by: Humberto Arocha
#    Finance by: HELADOS GILDA, C.A. http://www.heladosgilda.com.ve
#    Audited by: Humberto Arocha hbto@vauxoo.com
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
class wizard_account_balance_gene_2(osv.osv_memory):
    _name = "wizard.report.account.balance.gene.2"

    _columns = {
        'company_id': fields.many2one('res.company','Company',required=True),
        'account_list': fields.many2many ('account.account','rel_wizard_account','account_list','account_id','Root accounts',required=True),
        'filter': fields.selection([('bydate','By Date'),('byperiod','By Period'),('all','By Date and Period'),('none','No Filter')],'Date/Period Filter'),
        'fiscalyear': fields.many2one('account.fiscalyear','Fiscal year',help='Keep empty to use all open fiscal years to compute the balance',required=True),
        'periods': fields.many2many('account.period','rel_wizard_period','wizard_id','period_id','Periods',help='All periods in the fiscal year if empty'),
        'display_account': fields.selection([('bal_all','All'),('bal_solde', 'With balance'),('bal_mouvement','With movements')],'Display accounts'),
        'display_account_level': fields.integer('Up to level',help='Display accounts up to this level (0 to show all)'),
        'date_from': fields.date('Start date',required=True),
        'date_to': fields.date('End date',required=True),
        'tot_check': fields.boolean('Show Total'),
        'lab_str': fields.char('Description', size= 128),
        'inf_type': fields.selection([('bgen','Balance General'),('bcom','Balance Comprobacion'),('edogp','Estado Ganancias y Perdidas'),('bdl','Libro Diario Legal')],'Tipo Informe',required=True),
    }
    
    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-%m-%d'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
        'filter': lambda *a:'byperiod',
        'display_account_level': lambda *a: 0,
        'inf_type': lambda *a:'bcom',
        'company_id': lambda *a: 1,
        'fiscalyear': lambda *a: 1,
        'display_account': lambda *a:'bal_mouvement',
        
    }

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
        sql = """SELECT f.id, f.date_start, f.date_stop
            FROM account_fiscalyear f
            WHERE '%s' between f.date_start and f.date_stop """%(data['form']['date_from'])
        cr.execute(sql)
        res = cr.dictfetchall()
        if res:
            if (data['form']['date_to'] > res[0]['date_stop'] or data['form']['date_to'] < res[0]['date_start']):
                raise  wizard.except_wizard(_('UserError'),_('Date to must be set between %s and %s') % (res[0]['date_start'], res[0]['date_stop']))
            else:
                return 'report'
        else:
            raise wizard.except_wizard(_('UserError'),_('Date not in a defined fiscal year'))

    def print_report(self, cr, uid, ids,data, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids[0])
        return {'type': 'ir.actions.report.xml', 'report_name': 'account.account.balance.gene.2', 'datas': data}

wizard_account_balance_gene_2()


