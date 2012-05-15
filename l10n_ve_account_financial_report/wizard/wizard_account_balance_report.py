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

import wizard
import pooler
import time
from tools.translate import _

options_form = '''<?xml version="1.0"?>
<form string="General Account Balance [ Debit - Credit ] (One Column)">
    <field name="company_id"/>
    <newline/>
    <group colspan="4">
    <separator string="Accounts to include" colspan="4"/>
        <field name="account_list" nolabel="1" colspan="4" domain="[('company_id','=',company_id)]"/>
        <field name="display_account" required="True"/>
        <field name="display_account_level" required="True" />
    </group>
    <group colspan="4">
        <separator string="Period" colspan="4"/>
        <field name="fiscalyear"/>
        <newline/>
        <field name="state" required="True"/>
        <newline/>
        <group attrs="{'invisible':[('state','=','none')]}" colspan="4">
            <group attrs="{'invisible':[('state','=','byperiod')]}" colspan="4">
                <separator string="Date Filter" colspan="4"/>
                <field name="date_from"/>
                <field name="date_to"/>
            </group>
            <group attrs="{'invisible':[('state','=','bydate')]}" colspan="4">
                <separator string="Filter on Periods" colspan="4"/>
                <field name="periods" colspan="4" nolabel="1" domain="[('fiscalyear_id','=',fiscalyear)]"/>
            </group>
        </group>
    </group>
    <group colspan="4">
        <separator string="Total" colspan="4"/>
            <field name="tot_check"/>
            <field name="lab_str"/>
            <field name="inf_type"/>

    </group>    
</form>'''

options_fields = {
    'company_id': {'string': 'Company', 'type': 'many2one', 'relation': 'res.company', 'required': True},
    'account_list': {'string': 'Root accounts', 'type':'many2many', 'relation':'account.account', 'required':True ,'domain':[]},
    'state':{
        'string':"Date/Period Filter",
        'type':'selection',
        'selection':[('bydate','By Date'),('byperiod','By Period'),('all','By Date and Period'),('none','No Filter')],
        'default': lambda *a:'none'
    },
    'fiscalyear': {
        'string':'Fiscal year',
        'type':'many2one',
        'relation':'account.fiscalyear',
        'help':'Keep empty to use all open fiscal years to compute the balance'
    },
    'periods': {'string': 'Periods', 'type': 'many2many', 'relation': 'account.period', 'help': 'All periods in the fiscal year if empty'},
    'display_account':{'string':"Display accounts ", 'type':'selection', 'selection':[('bal_all','All'),('bal_solde', 'With balance'),('bal_mouvement','With movements')]},
    'display_account_level':{'string':"Up to level", 'type':'integer', 'default': lambda *a: 0, 'help': 'Display accounts up to this level (0 to show all)'},
    'date_from': {'string':"Start date", 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-01-01')},
    'date_to': {'string':"End date", 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-%m-%d')},
    'tot_check': {'string':'Show Total', 'type':'boolean'},    
    'lab_str': {'string': 'Description', 'type': 'char', 'size': 128},
    'inf_type':{
        'string':"Tipo Informe",
        'type':'selection',
        'selection':[('bgen','Balance General'),('bcom','Balance Comprobacion'),('edogp','Estado Ganancias y Perdidas')],
        'default': lambda *a:'bgen',
        'required':True
    },
    
    
}


class wizard_report(wizard.interface):

    def _get_defaults(self, cr, uid, data, context={}):
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


    def _check_state(self, cr, uid, data, context):
        if data['form']['state'] == 'bydate':
           self._check_date(cr, uid, data, context)
        return data['form']
    

    def _check_date(self, cr, uid, data, context):
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


    states = {

        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch': options_form, 'fields': options_fields, 'state':[('end','Cancel','gtk-cancel'),('report','Print','gtk-print')]}
        },
        'report': {
            'actions': [_check_state],
            'result': {'type':'print', 'report':'account.account.balance.gene', 'state':'end'}
        }
    }
wizard_report('account.balance.gene.report')

