# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
# Credits######################################################
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

import time
from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.osv import osv


class account_balance(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
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
            'get_informe_text': self.get_informe_text,
            'get_month': self.get_month,
            'exchange_name': self.exchange_name,
            'get_vat_by_country': self.get_vat_by_country,
        })
        self.context = context

    def get_vat_by_country(self, form):
        """
        Return the vat of the partner by country
        """
        rc_obj = self.pool.get('res.company')
        country_code = rc_obj.browse(self.cr, self.uid,
                                     form['company_id'][0]).partner_id.\
            country_id.code or ''
        string_vat = rc_obj.browse(self.cr, self.uid,
                                   form['company_id'][0]).partner_id.vat or ''
        if string_vat:
            if country_code == 'MX':
                return '%s' % (string_vat[2:])
            elif country_code == 'VE':
                return '- %s-%s-%s' % (string_vat[2:3],
                                       string_vat[3:11],
                                       string_vat[11:12])
            else:
                return string_vat
        else:
            return _('\nVAT OF COMPANY NOT AVAILABLE')

    def get_fiscalyear_text(self, form):
        """
        Returns the fiscal year text used on the report.
        """
        fiscalyear_obj = self.pool['account.fiscalyear']
        fiscalyear = None
        if form.get('fiscalyear'):
            fiscalyear = fiscalyear_obj.browse(
                self.cr, self.uid, form['fiscalyear'])
            return fiscalyear.name or fiscalyear.code
        else:
            fiscalyear = fiscalyear_obj.browse(
                self.cr, self.uid, fiscalyear_obj.find(self.cr, self.uid))
            return "%s*" % (fiscalyear.name or fiscalyear.code)

    def get_informe_text(self, form):
        """
        Returns the header text used on the report.
        """
        afr_id = form['afr_id'] and type(form['afr_id']) in (
            list, tuple) and form['afr_id'][0] or form['afr_id']
        if afr_id:
            name = self.pool.get('afr').browse(self.cr, self.uid, afr_id).name
        elif form['analytic_ledger'] and form['columns'] == 'four' \
                and form['inf_type'] == 'BS':
            name = _('Analytic Ledger')
        elif form['inf_type'] == 'BS':
            name = _('Balance Sheet')
        elif form['inf_type'] == 'IS':
            name = _('Income Statement')

        return name

    def get_month(self, form):
        '''
        return day, year and month
        '''
        if form['filter'] in ['bydate', 'all']:
            return _('From ') + self.formatLang(form['date_from'], date=True) \
                + _(' to ') + self.formatLang(form['date_to'], date=True)
        elif form['filter'] in ['byperiod', 'all']:
            aux = []
            period_obj = self.pool.get('account.period')

            for period in period_obj.browse(self.cr, self.uid,
                                            form['periods']):
                aux.append(period.date_start)
                aux.append(period.date_stop)
            sorted(aux)
            return _('From ') + self.formatLang(aux[0], date=True) + \
                _(' to ') + self.formatLang(aux[-1], date=True)

    def get_periods_and_date_text(self, form):
        """
        Returns the text with the periods/dates used on the report.
        """
        period_obj = self.pool['account.period']
        fiscalyear_obj = self.pool['account.fiscalyear']
        fiscalyear_id = form[
            'fiscalyear'] or fiscalyear_obj.find(self.cr, self.uid)
        period_ids = period_obj.search(self.cr, self.uid, [(
            'fiscalyear_id', '=', fiscalyear_id), ('special', '=', False)])
        if form['filter'] in ['byperiod', 'all']:
            period_ids = form['periods']
        periods_str = ', '.join([period.name or period.code
                                 for period in period_obj.browse(self.cr,
                                                                 self.uid,
                                                                 period_ids)])

        dates_str = None
        if form['filter'] in ['bydate', 'all']:
            dates_str = self.formatLang(form[
                                        'date_from'], date=True) + ' - ' + \
                self.formatLang(form['date_to'],
                                date=True) + ' '
        return {'periods': periods_str, 'date': dates_str}

    def special_period(self, periods):
        period_obj = self.pool.get('account.period')
        period_brw = period_obj.browse(self.cr, self.uid, periods)
        period_counter = [True for i in period_brw if not i.special]
        if not period_counter:
            return True
        return False

    def exchange_name(self, form):
        self.from_currency_id = self.\
            get_company_currency(form['company_id']
                                 and type(form['company_id']) in (list, tuple)
                                 and form['company_id'][0]
                                 or form['company_id'])
        if not form['currency_id']:
            self.to_currency_id = self.from_currency_id
        else:
            self.to_currency_id = form['currency_id'] \
                and type(form['currency_id']) in (list, tuple) \
                and form['currency_id'][0] or form['currency_id']
        return self.pool.get('res.currency').browse(self.cr, self.uid,
                                                    self.to_currency_id).name

    def exchange(self, from_amount):
        if self.from_currency_id == self.to_currency_id:
            return from_amount
        curr_obj = self.pool.get('res.currency')
        return curr_obj.compute(self.cr, self.uid, self.from_currency_id,
                                self.to_currency_id, from_amount)

    def get_company_currency(self, company_id):
        rc_obj = self.pool.get('res.company')
        return rc_obj.browse(self.cr, self.uid, company_id).currency_id.id

    def get_company_accounts(self, company_id, acc='credit'):
        rc_obj = self.pool.get('res.company')
        if acc == 'credit':
            return [brw.id for brw in rc_obj.browse(
                self.cr, self.uid,
                company_id).credit_account_ids]
        else:
            return [brw.id for brw in rc_obj.browse(
                self.cr, self.uid,
                company_id).debit_account_ids]

    def _get_partner_balance(self, account, init_period, ctx=None):
        res = []
        ctx = ctx or {}
        if account['type'] in ('other', 'liquidity', 'receivable', 'payable'):
            sql_query = """
                SELECT
                    CASE
                        WHEN aml.partner_id IS NOT NULL
                       THEN (SELECT name
                             FROM res_partner
                             WHERE aml.partner_id = id)
                    ELSE 'UNKNOWN'
                        END AS partner_name,
                    CASE
                        WHEN aml.partner_id IS NOT NULL
                       THEN aml.partner_id
                    ELSE 0
                        END AS p_idx,
                    %s,
                    %s,
                    %s,
                    %s
                FROM account_move_line AS aml
                INNER JOIN account_account aa ON aa.id = aml.account_id
                INNER JOIN account_move am ON am.id = aml.move_id
                %s
                GROUP BY p_idx, partner_name
                """

            WHERE_POSTED = ''
            if ctx.get('state', 'posted') == 'posted':
                WHERE_POSTED = "AND am.state = 'posted'"

            cur_periods = ', '.join([str(i) for i in ctx['periods']])
            init_periods = ', '.join([str(i) for i in init_period])

            WHERE = """
                WHERE aml.period_id IN (%s)
                    AND aa.id = %s
                    AND aml.state <> 'draft'
                    """ % (init_periods, account['id'])
            query_init = sql_query % ('SUM(aml.debit) AS init_dr',
                                      'SUM(aml.credit) AS init_cr',
                                      '0.0 AS bal_dr',
                                      '0.0 AS bal_cr',
                                      WHERE + WHERE_POSTED)

            WHERE = """
                WHERE aml.period_id IN (%s)
                    AND aa.id = %s
                    AND aml.state <> 'draft'
                    """ % (cur_periods, account['id'])

            query_bal = sql_query % ('0.0 AS init_dr',
                                     '0.0 AS init_cr',
                                     'SUM(aml.debit) AS bal_dr',
                                     'SUM(aml.credit) AS bal_cr',
                                     WHERE + WHERE_POSTED)

            query = '''
                SELECT
                    partner_name,
                    p_idx,
                    SUM(init_dr)-SUM(init_cr) AS balanceinit,
                    SUM(bal_dr) AS debit,
                    SUM(bal_cr) AS credit,
                    SUM(init_dr) - SUM(init_cr)
                        + SUM(bal_dr) - SUM(bal_cr) AS balance
                FROM (
                    SELECT
                    *
                    FROM (%s) vinit
                    UNION ALL (%s)
                ) v
                GROUP BY p_idx, partner_name
                ORDER BY partner_name
                ''' % (query_init, query_bal)

            self.cr.execute(query)
            res_dict = self.cr.dictfetchall()
            unknown = False
            for det in res_dict:
                i, d, c, b = det['balanceinit'], det[
                    'debit'], det['credit'], det['balance'],
                if not any([i, d, c, b]):
                    continue
                data = {
                    'partner_name': det['partner_name'],
                    'balanceinit': i,
                    'debit': d,
                    'credit': c,
                    'balance': b,
                }
                if not det['p_idx']:
                    unknown = data
                    continue
                res.append(data)
            unknown and res.append(unknown)
        return res

    def _get_analytic_ledger(self, account, ctx={}):
        res = []

        if account['type'] in ('other', 'liquidity', 'receivable', 'payable'):
            # ~ TODO: CUANDO EL PERIODO ESTE VACIO LLENARLO CON LOS PERIODOS
            # DEL EJERCICIO
            # ~ FISCAL, SIN LOS PERIODOS ESPECIALES
            periods = ', '.join([str(i) for i in ctx['periods']])
            # ~ periods = str(tuple(ctx['periods']))
            where = """where aml.period_id in (%s)
                       and aa.id = %s
                       and aml.state <> 'draft'""" % (periods, account['id'])
            if ctx.get('state', 'posted') == 'posted':
                where += "AND am.state = 'posted'"
            sql_detalle = """select aml.id as id,
                                aj.name as diario,
                                aa.name as descripcion,
                                (select name
                                 from res_partner
                                 where aml.partner_id = id) as partner,
                                aa.code as cuenta,
                                aml.name as name,
                                aml.ref as ref,
                                case when aml.debit is null
                                    then 0.00
                                    else aml.debit
                                end as debit,
                                case when aml.credit is null
                                    then 0.00
                                    else aml.credit
                                end as credit,
                                (select code
                                 from account_analytic_account
                                 where  aml.analytic_account_id = id)
                                     as analitica,
                                aml.date as date,
                                ap.name as periodo,
                                am.name as asiento
                            from account_move_line aml
                                inner join account_journal aj
                                    on aj.id = aml.journal_id
                                inner join account_account aa
                                    on aa.id = aml.account_id
                                inner join account_period ap
                                    on ap.id = aml.period_id
                                inner join account_move am
                                    on am.id = aml.move_id """ \
                            + where + """ order by date, am.name"""

            self.cr.execute(sql_detalle)
            resultat = self.cr.dictfetchall()
            balance = account['balanceinit']
            for det in resultat:
                balance += det['debit'] - det['credit']
                res.append({
                    'id': det['id'],
                    'date': det['date'],
                    'journal': det['diario'],
                    'partner': det['partner'],
                    'name': det['name'],
                    'entry': det['asiento'],
                    'ref': det['ref'],
                    'debit': det['debit'],
                    'credit': det['credit'],
                    'analytic': det['analitica'],
                    'period': det['periodo'],
                    'balance': balance,
                })
        return res

    def _get_journal_ledger(self, account, ctx={}):
        res = []
        am_obj = self.pool.get('account.move')
        print 'AM OBJ ', am_obj
        if account['type'] in ('other', 'liquidity', 'receivable', 'payable'):
            # ~ TODO: CUANDO EL PERIODO ESTE VACIO LLENARLO CON LOS PERIODOS
            # DEL EJERCICIO
            # ~ FISCAL, SIN LOS PERIODOS ESPECIALES
            periods = ', '.join([str(i) for i in ctx['periods']])
            # ~ periods = str(tuple(ctx['periods']))
            where = """where aml.period_id in (%s)
                       and aa.id = %s
                       and aml.state <> 'draft'""" % (periods, account['id'])
            if ctx.get('state', 'posted') == 'posted':
                where += "AND am.state = 'posted'"
            sql_detalle = """SELECT
                DISTINCT am.id as am_id,
                aj.name as diario,
                am.name as name,
                am.date as date,
                ap.name as periodo
                from account_move_line aml
                inner join account_journal aj on aj.id = aml.journal_id
                inner join account_account aa on aa.id = aml.account_id
                inner join account_period ap on ap.id = aml.period_id
                inner join account_move am on am.id = aml.move_id """ \
                + where + """ order by date, am.name"""

            self.cr.execute(sql_detalle)
            resultat = self.cr.dictfetchall()
            for det in resultat:
                res.append({
                    'am_id': det['am_id'],
                    'journal': det['diario'],
                    'name': det['name'],
                    'date': det['date'],
                    'period': det['periodo'],
                    'obj': am_obj.browse(self.cr, self.uid, det['am_id'])
                })
                print 'ACCOUNT NAME', am_obj.browse(self.cr, self.uid,
                                                    det['am_id']).name
        return res

    def lines(self, form, level=0):
        """
        Returns all the data needed for the report lines
        (account info plus debit/credit/balance in the selected period
        and the full year)
        """
        account_obj = self.pool.get('account.account')
        period_obj = self.pool.get('account.period')
        fiscalyear_obj = self.pool.get('account.fiscalyear')

        def _get_children_and_consol(cr, uid, ids, level, context={},
                                     change_sign=False):
            aa_obj = self.pool.get('account.account')
            ids2 = []
            for aa_brw in aa_obj.browse(cr, uid, ids, context):
                if aa_brw.child_id and aa_brw.level < level \
                        and aa_brw.type != 'consolidation':
                    if not change_sign:
                        ids2.append([aa_brw.id, True, False, aa_brw])
                    ids2 += _get_children_and_consol(
                        cr, uid, [x.id for x in aa_brw.child_id], level,
                        context, change_sign=change_sign)
                    if change_sign:
                        ids2.append(aa_brw.id)
                    else:
                        ids2.append([aa_brw.id, False, True, aa_brw])
                else:
                    if change_sign:
                        ids2.append(aa_brw.id)
                    else:
                        ids2.append([aa_brw.id, True, True, aa_brw])
            return ids2

        #######################################################################
        # CONTEXT FOR ENDIND BALANCE                                          #
        #######################################################################
        def _ctx_end(ctx):
            ctx_end = ctx
            ctx_end['filter'] = form.get('filter', 'all')
            ctx_end['fiscalyear'] = fiscalyear.id
            # ~ ctx_end['periods'] = period_obj.\
            # search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),
            #                            ('special','=',False)])

            if ctx_end['filter'] not in ['bydate', 'none']:
                special = self.special_period(form['periods'])
            else:
                special = False

            if form['filter'] in ['byperiod', 'all']:
                if special:
                    ctx_end['periods'] = period_obj.search(
                        self.cr, self.uid,
                        [('id', 'in', form['periods'] or ctx_end.get('periods',
                                                                     False))])
                else:
                    ctx_end['periods'] = period_obj.search(
                        self.cr, self.uid,
                        [('id', 'in', form['periods'] or ctx_end.get('periods',
                                                                     False)),
                         ('special', '=', False)])

            if form['filter'] in ['bydate', 'all', 'none']:
                ctx_end['date_from'] = form['date_from']
                ctx_end['date_to'] = form['date_to']

            return ctx_end.copy()

        def missing_period(ctx_init):

            ctx_init['fiscalyear'] = \
                fiscalyear_obj.search(self.cr, self.uid,
                                      [('date_stop', '<',
                                        fiscalyear.date_start)],
                                      order='date_stop') \
                and fiscalyear_obj.search(self.cr, self.uid,
                                          [('date_stop', '<',
                                            fiscalyear.date_start)],
                                          order='date_stop')[-1] or []
            ctx_init['periods'] = period_obj.search(
                self.cr, self.uid,
                [('fiscalyear_id', '=', ctx_init['fiscalyear']),
                 ('date_stop', '<', fiscalyear.date_start)])
            return ctx_init
        #######################################################################
        # CONTEXT FOR INITIAL BALANCE                                         #
        #######################################################################

        def _ctx_init(ctx):
            ctx_init = self.context.copy()
            ctx_init['filter'] = form.get('filter', 'all')
            ctx_init['fiscalyear'] = fiscalyear.id

            if form['filter'] in ['byperiod', 'all']:
                ctx_init['periods'] = form['periods']
                if not ctx_init['periods']:
                    ctx_init = missing_period(ctx_init.copy())
                date_start = min([period.date_start for period in period_obj.
                                  browse(self.cr, self.uid,
                                         ctx_init['periods'])])
                ctx_init['periods'] = period_obj.search(
                    self.cr, self.uid, [('fiscalyear_id', '=', fiscalyear.id),
                                        ('date_stop', '<=', date_start)])
            elif form['filter'] in ['bydate']:
                ctx_init['date_from'] = fiscalyear.date_start
                ctx_init['date_to'] = form['date_from']
                ctx_init['periods'] = period_obj.search(
                    self.cr, self.uid,
                    [('fiscalyear_id', '=', fiscalyear.id),
                     ('date_stop', '<=', ctx_init['date_to'])])
            elif form['filter'] == 'none':
                ctx_init['periods'] = period_obj.search(
                    self.cr, self.uid, [('fiscalyear_id', '=', fiscalyear.id),
                                        ('special', '=', True)])
                date_start = min([period.date_start for period in period_obj.
                                  browse(self.cr, self.uid,
                                         ctx_init['periods'])])
                ctx_init['periods'] = period_obj.search(
                    self.cr, self.uid, [('fiscalyear_id', '=', fiscalyear.id),
                                        ('date_start', '<=', date_start),
                                        ('special', '=', True)])

            return ctx_init.copy()

        def z(n):
            return abs(n) < 0.005 and 0.0 or n

        self.context['state'] = form['target_move'] or 'posted'

        self.from_currency_id = self.\
            get_company_currency(form['company_id']
                                 and type(form['company_id']) in (list, tuple)
                                 and form['company_id'][0]
                                 or form['company_id'])
        if not form['currency_id']:
            self.to_currency_id = self.from_currency_id
        else:
            self.to_currency_id = form['currency_id'] \
                and type(form['currency_id']) in (list, tuple) \
                and form['currency_id'][0] \
                or form['currency_id']

        if 'account_list' in form and form['account_list']:
            account_ids = form['account_list']
            account_list = form['account_list']
            del form['account_list']

        credit_account_ids = self.\
            get_company_accounts(form['company_id']
                                 and type(form['company_id']) in (list, tuple)
                                 and form['company_id'][0]
                                 or form['company_id'], 'credit')

        debit_account_ids = self.\
            get_company_accounts(form['company_id']
                                 and type(form['company_id']) in (list, tuple)
                                 and form['company_id'][0]
                                 or form['company_id'], 'debit')

        if form.get('fiscalyear'):
            if type(form.get('fiscalyear')) in (list, tuple):
                fiscalyear = form['fiscalyear'] and form['fiscalyear'][0]
            elif type(form.get('fiscalyear')) in (int,):
                fiscalyear = form['fiscalyear']
        fiscalyear = fiscalyear_obj.browse(self.cr, self.uid, fiscalyear)

        ################################################################
        # Get the accounts                                             #
        ################################################################
        all_account_ids = _get_children_and_consol(
            self.cr, self.uid, account_ids, 100, self.context)

        account_ids = _get_children_and_consol(
            self.cr, self.uid, account_ids,
            form['display_account_level']
            and form['display_account_level']
            or 100, self.context)

        credit_account_ids = _get_children_and_consol(
            self.cr, self.uid, credit_account_ids, 100, self.context,
            change_sign=True)

        debit_account_ids = _get_children_and_consol(
            self.cr, self.uid, debit_account_ids, 100, self.context,
            change_sign=True)

        credit_account_ids = list(set(
            credit_account_ids) - set(debit_account_ids))
        #
        # Generate the report lines (checking each account)
        #

        tot_check = False

        if not form['periods']:
            form['periods'] = period_obj.search(
                self.cr, self.uid, [('fiscalyear_id', '=', fiscalyear.id),
                                    ('special', '=', False)],
                order='date_start asc')
            if not form['periods']:
                raise osv.except_osv(_('UserError'), _(
                    'The Selected Fiscal Year Does not have Regular Periods'))

        if form['columns'] == 'qtr':
            period_ids = period_obj.search(
                self.cr, self.uid, [('fiscalyear_id', '=', fiscalyear.id),
                                    ('special', '=', False)],
                order='date_start asc')
            a = 0
            l = []
            p = []
            for x in period_ids:
                a += 1
                if a < 3:
                    l.append(x)
                else:
                    l.append(x)
                    p.append(l)
                    l = []
                    a = 0
            tot_bal1 = 0.0
            tot_bal2 = 0.0
            tot_bal3 = 0.0
            tot_bal4 = 0.0
            tot_bal5 = 0.0
        elif form['columns'] == 'thirteen':
            period_ids = period_obj.search(
                self.cr, self.uid, [('fiscalyear_id', '=', fiscalyear.id),
                                    ('special', '=', False)],
                order='date_start asc')
            tot_bal1 = 0.0
            tot_bal1 = 0.0
            tot_bal2 = 0.0
            tot_bal3 = 0.0
            tot_bal4 = 0.0
            tot_bal5 = 0.0
            tot_bal6 = 0.0
            tot_bal7 = 0.0
            tot_bal8 = 0.0
            tot_bal9 = 0.0
            tot_bal10 = 0.0
            tot_bal11 = 0.0
            tot_bal12 = 0.0
            tot_bal13 = 0.0
        else:
            ctx_end = _ctx_end(self.context.copy())
            tot_bin = 0.0
            tot_deb = 0.0
            tot_crd = 0.0
            tot_ytd = 0.0
            tot_eje = 0.0

        res = {}
        result_acc = []
        tot = {}

        ###############################################################
        # Calculations of credit, debit and balance,
        # without repeating operations.
        ###############################################################

        account_black_ids = account_obj.search(
            self.cr, self.uid, (
                [('id', 'in', [i[0] for i in all_account_ids]),
                 ('type', 'not in', ('view', 'consolidation'))]))

        account_not_black_ids = account_obj.search(
            self.cr, self.uid, ([('id', 'in', [i[0] for i in all_account_ids]),
                                 ('type', '=', 'view')]))

        acc_cons_ids = account_obj.search(
            self.cr, self.uid, ([('id', 'in', [i[0] for i in all_account_ids]),
                                 ('type', 'in', ('consolidation',))]))

        account_consol_ids = acc_cons_ids and account_obj.\
            _get_children_and_consol(self.cr, self.uid, acc_cons_ids) or []

        account_black_ids += account_obj.search(self.cr, self.uid, (
            [('id', 'in', account_consol_ids),
             ('type', 'not in',
              ('view', 'consolidation'))]))

        account_black_ids = list(set(account_black_ids))

        c_account_not_black_ids = account_obj.search(self.cr, self.uid, ([
            ('id', 'in', account_consol_ids),
            ('type', '=', 'view')]))
        delete_cons = False
        if c_account_not_black_ids:
            delete_cons = set(account_not_black_ids) & set(
                c_account_not_black_ids) and True or False
            account_not_black_ids = list(
                set(account_not_black_ids) - set(c_account_not_black_ids))

        # This could be done quickly with a sql sentence
        account_not_black = account_obj.browse(
            self.cr, self.uid, account_not_black_ids)
        account_not_black.sort(key=lambda x: x.level)
        account_not_black.reverse()
        account_not_black_ids = [i.id for i in account_not_black]

        c_account_not_black = account_obj.browse(
            self.cr, self.uid, c_account_not_black_ids)
        c_account_not_black.sort(key=lambda x: x.level)
        c_account_not_black.reverse()
        c_account_not_black_ids = [i.id for i in c_account_not_black]

        if delete_cons:
            account_not_black_ids = c_account_not_black_ids + \
                account_not_black_ids
            account_not_black = c_account_not_black + account_not_black
        else:
            acc_cons_brw = account_obj.browse(
                self.cr, self.uid, acc_cons_ids)
            acc_cons_brw.sort(key=lambda x: x.level)
            acc_cons_brw.reverse()
            acc_cons_ids = [i.id for i in acc_cons_brw]

            account_not_black_ids = c_account_not_black_ids + \
                acc_cons_ids + account_not_black_ids
            account_not_black = c_account_not_black + \
                acc_cons_brw + account_not_black

        all_account_period = {}  # All accounts per period

        # Iteration limit depending on the number of columns
        if form['columns'] == 'thirteen':
            limit = 13
        elif form['columns'] == 'qtr':
            limit = 5
        else:
            limit = 1

        for p_act in range(limit):
            if limit != 1:
                if p_act == limit - 1:
                    form['periods'] = period_ids
                else:
                    if form['columns'] == 'thirteen':
                        form['periods'] = [period_ids[p_act]]
                    elif form['columns'] == 'qtr':
                        form['periods'] = p[p_act]

            if form['inf_type'] == 'IS':
                ctx_to_use = _ctx_end(self.context.copy())
            else:
                ctx_i = _ctx_init(self.context.copy())
                ctx_to_use = _ctx_end(self.context.copy())

            account_black = account_obj.browse(
                self.cr, self.uid, account_black_ids, ctx_to_use)

            if form['inf_type'] == 'BS':
                account_black_init = account_obj.browse(
                    self.cr, self.uid, account_black_ids, ctx_i)

            # ~ Black
            dict_black = {}
            for i in account_black:
                d = i.debit
                c = i.credit
                dict_black[i.id] = {
                    'obj': i,
                    'debit': d,
                    'credit': c,
                    'balance': d - c
                }
                if form['inf_type'] == 'BS':
                    dict_black.get(i.id)['balanceinit'] = 0.0

            # If the report is a balance sheet
            # Balanceinit values are added to the dictionary
            if form['inf_type'] == 'BS':
                for i in account_black_init:
                    dict_black.get(i.id)['balanceinit'] = i.balance

            # ~ Not black
            dict_not_black = {}
            for i in account_not_black:
                dict_not_black[i.id] = {
                    'obj': i, 'debit': 0.0, 'credit': 0.0, 'balance': 0.0}
                if form['inf_type'] == 'BS':
                    dict_not_black.get(i.id)['balanceinit'] = 0.0

            all_account = dict_black.copy(
            )  # It makes a copy because they modify

            for acc_id in account_not_black_ids:
                acc_childs = dict_not_black.get(acc_id).get('obj').\
                    type == 'view' \
                    and dict_not_black.get(acc_id).get('obj').child_id \
                    or dict_not_black.get(acc_id).get('obj').child_consol_ids
                for child_id in acc_childs:
                    if child_id.type == 'consolidation' and delete_cons:
                        continue
                    dict_not_black.get(acc_id)['debit'] += all_account.get(
                        child_id.id).get('debit')
                    dict_not_black.get(acc_id)['credit'] += all_account.get(
                        child_id.id).get('credit')
                    dict_not_black.get(acc_id)['balance'] += all_account.get(
                        child_id.id).get('balance')
                    if form['inf_type'] == 'BS':
                        dict_not_black.get(acc_id)['balanceinit'] += \
                            all_account.get(child_id.id).get('balanceinit')
                all_account[acc_id] = dict_not_black[acc_id]

            if p_act == limit - 1:
                all_account_period['all'] = all_account
            else:
                if form['columns'] == 'thirteen':
                    all_account_period[p_act] = all_account
                elif form['columns'] == 'qtr':
                    all_account_period[p_act] = all_account

        ###############################################################
        # End of the calculations of credit, debit and balance
        #
        ###############################################################

        for aa_id in account_ids:
            id = aa_id[0]
            if aa_id[3].type == 'consolidation' and delete_cons:
                continue
            #
            # Check if we need to include this level
            #
            if not form['display_account_level'] \
                    or aa_id[3].level <= form['display_account_level']:
                res = {
                    'id': id,
                    'type': aa_id[3].type,
                    'code': aa_id[3].code,
                    'name': (aa_id[2] and not aa_id[1])
                    and 'TOTAL %s' % (aa_id[3].name.upper())
                    or aa_id[3].name,
                    'parent_id': aa_id[3].parent_id and aa_id[3].parent_id.id,
                    'level': aa_id[3].level,
                    'label': aa_id[1],
                    'total': aa_id[2],
                    'change_sign': credit_account_ids
                    and (id in credit_account_ids and -1 or 1) or 1
                }

                if form['columns'] == 'qtr':
                    for pn in range(1, 5):

                        if form['inf_type'] == 'IS':
                            d, c, b = map(z, [
                                          all_account_period.get(pn - 1).
                                          get(id).get('debit', 0.0),
                                          all_account_period.get(pn - 1).
                                          get(id).get('credit', 0.0),
                                          all_account_period.get(pn - 1).
                                          get(id).get('balance', 0.0)])
                            res.update({
                                'dbr%s' % pn: self.exchange(d),
                                'cdr%s' % pn: self.exchange(c),
                                'bal%s' % pn: self.exchange(b),
                            })
                        else:
                            i, d, c = map(z, [
                                          all_account_period.get(pn - 1).
                                          get(id).get('balanceinit', 0.0),
                                          all_account_period.get(pn - 1).
                                          get(id).get('debit', 0.0),
                                          all_account_period.get(pn - 1).
                                          get(id).get('credit', 0.0)])
                            b = z(i + d - c)
                            res.update({
                                'dbr%s' % pn: self.exchange(d),
                                'cdr%s' % pn: self.exchange(c),
                                'bal%s' % pn: self.exchange(b),
                            })

                    if form['inf_type'] == 'IS':
                        d, c, b = map(z, [
                                      all_account_period.get('all').get(id).
                                      get('debit', 0.0),
                                      all_account_period.get('all').get(id).
                                      get('credit', 0.0),
                                      all_account_period.get('all').get(id).
                                      get('balance')])
                        res.update({
                            'dbr5': self.exchange(d),
                            'cdr5': self.exchange(c),
                            'bal5': self.exchange(b),
                        })
                    else:
                        i, d, c = map(z, [
                                      all_account_period.get('all').get(id).
                                      get('balanceinit', 0.0),
                                      all_account_period.get('all').get(id).
                                      get('debit', 0.0),
                                      all_account_period.get('all').get(id).
                                      get('credit', 0.0)])
                        b = z(i + d - c)
                        res.update({
                            'dbr5': self.exchange(d),
                            'cdr5': self.exchange(c),
                            'bal5': self.exchange(b),
                        })

                elif form['columns'] == 'thirteen':
                    pn = 1
                    for p_num in range(12):

                        if form['inf_type'] == 'IS':
                            d, c, b = map(z, [
                                          all_account_period.get(p_num).
                                          get(id).get('debit', 0.0),
                                          all_account_period.get(p_num).
                                          get(id).get('credit', 0.0),
                                          all_account_period.get(p_num).
                                          get(id).get('balance', 0.0)])
                            res.update({
                                'dbr%s' % pn: self.exchange(d),
                                'cdr%s' % pn: self.exchange(c),
                                'bal%s' % pn: self.exchange(b),
                            })
                        else:
                            i, d, c = map(z, [
                                          all_account_period.get(p_num).
                                          get(id).get('balanceinit', 0.0),
                                          all_account_period.get(p_num).
                                          get(id).get('debit', 0.0),
                                          all_account_period.get(p_num).
                                          get(id).get('credit', 0.0)])
                            b = z(i + d - c)
                            res.update({
                                'dbr%s' % pn: self.exchange(d),
                                'cdr%s' % pn: self.exchange(c),
                                'bal%s' % pn: self.exchange(b),
                            })

                        pn += 1

                    if form['inf_type'] == 'IS':
                        d, c, b = map(z, [
                                      all_account_period.get('all').get(id).
                                      get('debit', 0.0),
                                      all_account_period.get('all').get(id).
                                      get('credit', 0.0),
                                      all_account_period.get('all').get(id).
                                      get('balance', 0.0)])
                        res.update({
                            'dbr13': self.exchange(d),
                            'cdr13': self.exchange(c),
                            'bal13': self.exchange(b),
                        })
                    else:
                        i, d, c = map(z, [
                                      all_account_period.get('all').get(id).
                                      get('balanceinit', 0.0),
                                      all_account_period.get('all').get(id).
                                      get('debit', 0.0),
                                      all_account_period.get('all').get(id).
                                      get('credit', 0.0)])
                        b = z(i + d - c)
                        res.update({
                            'dbr13': self.exchange(d),
                            'cdr13': self.exchange(c),
                            'bal13': self.exchange(b),
                        })

                else:
                    i, d, c = map(z, [
                                  all_account_period.get('all').get(id).
                                  get('balanceinit', 0.0),
                                  all_account_period.get('all').get(id).
                                  get('debit', 0.0),
                                  all_account_period.get('all').get(id).
                                  get('credit', 0.0)])
                    b = z(i + d - c)
                    res.update({
                        'balanceinit': self.exchange(i),
                        'debit': self.exchange(d),
                        'credit': self.exchange(c),
                        'ytd': self.exchange(d - c),
                    })

                    if form['inf_type'] == 'IS' and form['columns'] == 'one':
                        res.update({
                            'balance': self.exchange(d - c),
                        })
                    else:
                        res.update({
                            'balance': self.exchange(b),
                        })

                #
                # Check whether we must include this line in the report or not
                #
                to_include = False

                if form['columns'] in ('thirteen', 'qtr'):
                    to_test = [False]
                    if form['display_account'] == 'mov' and aa_id[3].parent_id:
                        # Include accounts with movements
                        for x in range(pn - 1):
                            to_test.append(res.get(
                                'dbr%s' % x, 0.0) >= 0.005 and True or False)
                            to_test.append(res.get(
                                'cdr%s' % x, 0.0) >= 0.005 and True or False)
                        if any(to_test):
                            to_include = True

                    elif form['display_account'] == 'bal' and aa_id[3].\
                            parent_id:
                        # Include accounts with balance
                        for x in range(pn - 1):
                            to_test.append(res.get(
                                'bal%s' % x, 0.0) >= 0.005 and True or False)
                        if any(to_test):
                            to_include = True

                    elif form['display_account'] == 'bal_mov' and aa_id[3].\
                            parent_id:
                        # Include accounts with balance or movements
                        for x in range(pn - 1):
                            to_test.append(res.get(
                                'bal%s' % x, 0.0) >= 0.005 and True or False)
                            to_test.append(res.get(
                                'dbr%s' % x, 0.0) >= 0.005 and True or False)
                            to_test.append(res.get(
                                'cdr%s' % x, 0.0) >= 0.005 and True or False)
                        if any(to_test):
                            to_include = True
                    else:
                        # Include all accounts
                        to_include = True

                else:

                    if form['display_account'] == 'mov' and aa_id[3].parent_id:
                        # Include accounts with movements
                        if abs(d) >= 0.005 or abs(c) >= 0.005:
                            to_include = True
                    elif form['display_account'] == 'bal' and aa_id[3].\
                            parent_id:
                        # Include accounts with balance
                        if abs(b) >= 0.005:
                            to_include = True
                    elif form['display_account'] == 'bal_mov' and aa_id[3].\
                            parent_id:
                        # Include accounts with balance or movements
                        if abs(b) >= 0.005 \
                                or abs(d) >= 0.005 \
                                or abs(c) >= 0.005:
                            to_include = True
                    else:
                        # Include all accounts
                        to_include = True

                # ~ ANALYTIC LEDGER
                if to_include and form['analytic_ledger'] \
                    and form['columns'] == 'four' \
                    and form['inf_type'] == 'BS' \
                    and res['type'] in ('other', 'liquidity',
                                        'receivable', 'payable'):
                    res['mayor'] = self._get_analytic_ledger(res, ctx=ctx_end)
                elif to_include and form['journal_ledger'] \
                    and form['columns'] == 'four' \
                    and form['inf_type'] == 'BS' \
                    and res['type'] in ('other', 'liquidity',
                                        'receivable', 'payable'):
                    res['journal'] = self._get_journal_ledger(res, ctx=ctx_end)
                elif to_include and form['partner_balance'] \
                    and form['columns'] == 'four' \
                    and form['inf_type'] == 'BS' \
                    and res['type'] in ('other', 'liquidity',
                                        'receivable', 'payable'):
                    res['partner'] = self._get_partner_balance(
                        res, ctx_i['periods'], ctx=ctx_end)
                else:
                    res['mayor'] = []

                if to_include:
                    result_acc.append(res)
                    #
                    # Check whether we must sumarize this line in the report
                    # or not
                    #
                    if form['tot_check'] and (res['id'] in account_list) \
                            and (res['id'] not in tot):
                        if form['columns'] == 'qtr':
                            tot_check = True
                            tot[res['id']] = True
                            tot_bal1 += res.get('bal1', 0.0)
                            tot_bal2 += res.get('bal2', 0.0)
                            tot_bal3 += res.get('bal3', 0.0)
                            tot_bal4 += res.get('bal4', 0.0)
                            tot_bal5 += res.get('bal5', 0.0)

                        elif form['columns'] == 'thirteen':
                            tot_check = True
                            tot[res['id']] = True
                            tot_bal1 += res.get('bal1', 0.0)
                            tot_bal2 += res.get('bal2', 0.0)
                            tot_bal3 += res.get('bal3', 0.0)
                            tot_bal4 += res.get('bal4', 0.0)
                            tot_bal5 += res.get('bal5', 0.0)
                            tot_bal6 += res.get('bal6', 0.0)
                            tot_bal7 += res.get('bal7', 0.0)
                            tot_bal8 += res.get('bal8', 0.0)
                            tot_bal9 += res.get('bal9', 0.0)
                            tot_bal10 += res.get('bal10', 0.0)
                            tot_bal11 += res.get('bal11', 0.0)
                            tot_bal12 += res.get('bal12', 0.0)
                            tot_bal13 += res.get('bal13', 0.0)
                        else:
                            tot_check = True
                            tot[res['id']] = True
                            tot_bin += res['balanceinit']
                            tot_deb += res['debit']
                            tot_crd += res['credit']
                            tot_ytd += res['ytd']
                            tot_eje += res['balance']

        if tot_check:
            str_label = form['lab_str']
            res2 = {
                'type': 'view',
                'name': 'TOTAL %s' % (str_label),
                'label': False,
                'total': True,
            }
            if form['columns'] == 'qtr':
                res2.update(dict(
                            bal1=z(tot_bal1),
                            bal2=z(tot_bal2),
                            bal3=z(tot_bal3),
                            bal4=z(tot_bal4),
                            bal5=z(tot_bal5),))
            elif form['columns'] == 'thirteen':
                res2.update(dict(
                            bal1=z(tot_bal1),
                            bal2=z(tot_bal2),
                            bal3=z(tot_bal3),
                            bal4=z(tot_bal4),
                            bal5=z(tot_bal5),
                            bal6=z(tot_bal6),
                            bal7=z(tot_bal7),
                            bal8=z(tot_bal8),
                            bal9=z(tot_bal9),
                            bal10=z(tot_bal10),
                            bal11=z(tot_bal11),
                            bal12=z(tot_bal12),
                            bal13=z(tot_bal13),))

            else:
                res2.update({
                    'balanceinit': tot_bin,
                    'debit': tot_deb,
                    'credit': tot_crd,
                    'ytd': tot_ytd,
                    'balance': tot_eje,
                })

            result_acc.append(res2)
        return result_acc

report_sxw.report_sxw(
    'report.afr.1cols',
    'wizard.report',
    'account_financial_report/report/balance_full.rml',
    parser=account_balance,
    header=False)

report_sxw.report_sxw(
    'report.afr.2cols',
    'wizard.report',
    'account_financial_report/report/balance_full_2_cols.rml',
    parser=account_balance,
    header=False)

report_sxw.report_sxw(
    'report.afr.4cols',
    'wizard.report',
    'account_financial_report/report/balance_full_4_cols.rml',
    parser=account_balance,
    header=False)

report_sxw.report_sxw(
    'report.afr.analytic.ledger',
    'wizard.report',
    'account_financial_report/report/balance_full_4_cols_analytic_ledger.rml',
    parser=account_balance,
    header=False)

report_sxw.report_sxw(
    'report.afr.partner.balance',
    'wizard.report',
    'account_financial_report/report/balance_full_4_cols_partner_balance.rml',
    parser=account_balance,
    header=False)

report_sxw.report_sxw(
    'report.afr.journal.ledger',
    'wizard.report',
    'account_financial_report/report/balance_full_4_cols_journal_ledger.rml',
    parser=account_balance,
    header=False)

report_sxw.report_sxw(
    'report.afr.5cols',
    'wizard.report',
    'account_financial_report/report/balance_full_5_cols.rml',
    parser=account_balance,
    header=False)

report_sxw.report_sxw(
    'report.afr.qtrcols',
    'wizard.report',
    'account_financial_report/report/balance_full_qtr_cols.rml',
    parser=account_balance,
    header=False)

report_sxw.report_sxw(
    'report.afr.13cols',
    'wizard.report',
    'account_financial_report/report/balance_full_13_cols.rml',
    parser=account_balance,
    header=False)
