# -*- coding: utf-8 -*-

import calendar

import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
from odoo import api, models, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import AccessError, UserError

D_LEDGER = {'general': {'name': _('General Ledger'),
                        'group_by': 'account_id',
                        'model': 'account.account',
                        'short': 'code',
                        },
            'partner': {'name': _('Partner Ledger'),
                        'group_by': 'partner_id',
                        'model': 'res.partner',
                        'short': 'name',
                        },
            'journal': {'name': _('Journal Ledger'),
                        'group_by': 'journal_id',
                        'model': 'account.journal',
                        'short': 'code',
                        },
            'open': {'name': _('Open Ledger'),
                     'group_by': 'account_id',
                     'model': 'account.account',
                     'short': 'code',
                     },
            'aged': {'name': _('Aged Balance'),
                     'group_by': 'partner_id',
                     'model': 'res.partner',
                     'short': 'name',
                     },
            }


class AccountStandardLedgerPeriode(models.TransientModel):
    _name = 'account.report.standard.ledger.periode'

    name = fields.Char('Name')
    date_from = fields.Datetime('Date from')
    date_to = fields.Datetime('Date to')


class AccountStandardLedgerReport(models.TransientModel):
    _name = 'account.report.standard.ledger.report'

    name = fields.Char()
    report_object_ids = fields.One2many('account.report.standard.ledger.report.object', 'report_id')
    report_name = fields.Char()
    line_total_ids = fields.Many2many('account.report.standard.ledger.line', relation='table_standard_report_line_total')
    line_super_total_id = fields.Many2one('account.report.standard.ledger.line')
    print_time = fields.Char()
    date_from = fields.Date(string='Start Date', help='Use to compute initial balance.')
    date_to = fields.Date(string='End Date', help='Use to compute the entrie matched with futur.')


class AccountStandardLedgerLines(models.TransientModel):
    _name = 'account.report.standard.ledger.line'
    _order = 'id'  # ,move_id,account_id #type,date,move_line_id_id,
    _rec_name = 'move_id'

    report_id = fields.Many2one('account.report.standard.ledger.report')
    account_id = fields.Many2one('account.account', 'Account')
    type = fields.Selection([('0_init', 'Initial'), ('1_init_line', 'Init Line'), ('2_line', 'Line'), ('3_compact',
                                                                                                       'Compacted'), ('4_total', 'Total'), ('5_super_total', 'Super Total')], string='Type')
    type_view = fields.Selection([('init', 'Init'), ('normal', 'Normal'), ('total', 'Total')])
    journal_id = fields.Many2one('account.journal', 'Journal')
    partner_id = fields.Many2one('res.partner', 'Partner')
    group_by_key = fields.Char()
    move_id = fields.Many2one('account.move', 'Entrie')
    move_line_id = fields.Many2one('account.move.line')
    date = fields.Date()
    date_maturity = fields.Date('Due Date')
    debit = fields.Float(default=0.0, digits=dp.get_precision('Account'))
    credit = fields.Float(default=0.0, digits=dp.get_precision('Account'))
    balance = fields.Float(default=0.0, digits=dp.get_precision('Account'))
    cumul_balance = fields.Float(default=0.0, digits=dp.get_precision('Account'), string='Balance')
    full_reconcile_id = fields.Many2one('account.full.reconcile', 'Match.')
    reconciled = fields.Boolean('Reconciled')
    report_object_id = fields.Many2one('account.report.standard.ledger.report.object')

    current = fields.Float(default=0.0, digits=dp.get_precision('Account'), string='Not due')
    age_30_days = fields.Float(default=0.0, digits=dp.get_precision('Account'), string='30 days')
    age_60_days = fields.Float(default=0.0, digits=dp.get_precision('Account'), string='60 days')
    age_90_days = fields.Float(default=0.0, digits=dp.get_precision('Account'), string='90 days')
    age_120_days = fields.Float(default=0.0, digits=dp.get_precision('Account'), string='120 days')
    older = fields.Float(default=0.0, digits=dp.get_precision('Account'), string='Older')

    company_currency_id = fields.Many2one('res.currency')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(AccountStandardLedgerLines, self).read_group(domain, fields, groupby, offset, limit=limit, orderby=orderby, lazy=lazy)
        if 'cumul_balance' in fields and 'debit' in fields and 'credit' in fields:
            for line in res:
                line['cumul_balance'] = line['debit'] - line['credit']
        return res


class AccountStandardLedgerReportObject(models.TransientModel):
    _name = 'account.report.standard.ledger.report.object'
    _order = 'name, id'

    name = fields.Char()
    object_id = fields.Integer()
    report_id = fields.Many2one('account.report.standard.ledger.report')
    line_ids = fields.One2many('account.report.standard.ledger.line', 'report_object_id')
    account_id = fields.Many2one('account.account', 'Account')
    journal_id = fields.Many2one('account.journal', 'Journal')
    partner_id = fields.Many2one('res.partner', 'Partner')


class AccountStandardLedger(models.TransientModel):
    _name = 'account.report.standard.ledger'
    _description = 'Account Standard Ledger'

    def _get_periode_date(self):
        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format

        today_year = fields.datetime.now().year

        last_day = self.company_id.fiscalyear_last_day or 31
        last_month = self.company_id.fiscalyear_last_month or 12
        periode_obj = self.env['account.report.standard.ledger.periode']
        periode_obj.search([]).unlink()
        periode_ids = periode_obj
        for year in range(today_year, today_year - 4, -1):
            date_from = datetime(year - 1, last_month, last_day) + timedelta(days=1)
            date_to = datetime(year, last_month, last_day)
            user_periode = "%s - %s" % (date_from.strftime(date_format),
                                        date_to.strftime(date_format),
                                        )
            vals = {
                'name': user_periode,
                'date_from': date_from.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'date_to': date_to.strftime(DEFAULT_SERVER_DATE_FORMAT), }
            periode_ids += periode_obj.create(vals)
        return False

    name = fields.Char(default='Standard Report')
    type_ledger = fields.Selection([('general', 'General Ledger'), ('partner', 'Partner Ledger'), ('journal', 'Journal Ledger'), ('open', 'Open Ledger'), ('aged', 'Aged Balance')], string='Type', default='general', required=True,
                                   help=' * General Ledger : Journal entries group by account\n'
                                   ' * Partner Leger : Journal entries group by partner, with only payable/recevable accounts\n'
                                   ' * Journal Ledger : Journal entries group by journal, without initial balance\n'
                                   ' * Open Ledger : Openning journal at Start date\n')
    summary = fields.Boolean('Trial Balance', default=False,
                             help=' * Check : generate a trial balance.\n'
                             ' * Uncheck : detail report.\n')
    amount_currency = fields.Boolean("With Currency", help="It adds the currency column on report if the currency differs from the company currency.")
    reconciled = fields.Boolean('With Reconciled Entries', default=True,
                                help='Only for entrie with a payable/receivable account.\n'
                                ' * Check this box to see un-reconcillied and reconciled entries with payable.\n'
                                ' * Uncheck to see only un-reconcillied entries. Can be use only with parnter ledger.\n')
    partner_select_ids = fields.Many2many(comodel_name='res.partner', string='Partners', domain=['|', ('is_company', '=', True), ('parent_id', '=', False)], help='If empty, get all partners')
    account_methode = fields.Selection([('include', 'Include'), ('exclude', 'Exclude')], string="Methode")
    account_in_ex_clude = fields.Many2many(comodel_name='account.account', string='Accounts', help='If empty, get all accounts')
    init_balance_history = fields.Boolean('Initial balance with history.', default=True,
                                          help=' * Check this box if you need to report all the debit and the credit sum before the Start Date.\n'
                                          ' * Uncheck this box to report only the balance before the Start Date\n')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True,
                                          help='Utility field to express amount currency', store=True)
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True, default=lambda self: self.env['account.journal'].search([('company_id', '=', self.env.user.company_id.id)]),
                                   help='Select journal, for the Open Ledger you need to set all journals.')
    date_from = fields.Date(string='Start Date', help='Use to compute initial balance.')
    date_to = fields.Date(string='End Date', help='Use to compute the entrie matched with futur.')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    periode_date = fields.Many2one('account.report.standard.ledger.periode', 'Periode', default=_get_periode_date, help="Auto complete Start and End date.")
    month_selec = fields.Selection([(1, '01 Junary'), (2, '02 Febuary'), (3, '03 March'), (4, '04 April'), (5, '05 May'), (6, '06 June'),
                                    (7, '07 Jully'), (8, '08 August'), (9, '09 September'), (10, '10 October'), (11, '11 November'), (12, '12 December')],
                                   string='Month')
    result_selection = fields.Selection([('customer', 'Customer'),
                                         ('supplier', 'Supplier'),
                                         ('customer_supplier', 'Receivable and Payable Accounts')
                                         ], string="Partner's", required=True, default='supplier')
    report_name = fields.Char('Report Name')
    compact_account = fields.Boolean('Compacte account.', default=False)
    report_id = fields.Many2one('account.report.standard.ledger.report')
    account_ids = fields.Many2many('account.account', relation='table_standard_report_accounts')
    partner_ids = fields.Many2many('res.partner', relation='table_standard_report_partner')
    type = fields.Selection([('account', 'Account'), ('partner', 'Partner'), ('journal', 'Journal')])

    @api.onchange('account_in_ex_clude')
    def on_change_summary(self):
        if self.account_in_ex_clude:
            self.account_methode = 'include'
        else:
            self.account_methode = False

    @api.onchange('type_ledger')
    def on_change_type_ledger(self):
        if self.type_ledger in ('partner', 'journal', 'open', 'aged'):
            self.compact_account = False
        if self.type_ledger == 'aged':
            self.date_from = False
            self.reconciled = False
        else:
            self.on_change_periode_date()
            self.on_change_month_selec()
        if self.type_ledger not in ('partner', 'aged',):
            self.reconciled = True
            return {'domain': {'account_in_ex_clude': []}}
        self.account_in_ex_clude = False
        if self.result_selection == 'suplier':
            return {'domain': {'account_in_ex_clude': [('type_third_parties', '=', 'supplier')]}}
        if self.result_selection == 'customer':
            return {'domain': {'account_in_ex_clude': [('type_third_parties', '=', 'customer')]}}
        return {'domain': {'account_in_ex_clude': [('type_third_parties', 'in', ('supplier', 'customer'))]}}

    @api.onchange('periode_date')
    def on_change_periode_date(self):
        if self.periode_date:
            self.date_from = self.periode_date.date_from
            self.date_to = self.periode_date.date_to
            if self.month_selec:
                self.on_change_month_selec()

    @api.onchange('month_selec')
    def on_change_month_selec(self):
        if self.periode_date and self.month_selec:
            date_from = datetime.strptime(self.periode_date.date_from, DEFAULT_SERVER_DATETIME_FORMAT)
            date_from = datetime(date_from.year, self.month_selec, 1)
            date_to = datetime(date_from.year, self.month_selec, calendar.monthrange(date_from.year, self.month_selec)[1])
            self.date_from = date_from.strftime(DEFAULT_SERVER_DATE_FORMAT)
            self.date_to = date_to.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif self.periode_date and not self.month_selec:
            self.on_change_periode_date()

    def action_view_lines(self):
        self.ensure_one()
        self._compute_data()
        return {
            'name': _("Ledger Lines"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('account_standard_report.view_aged_tree').id if self.type_ledger == 'aged' else False, 'tree'), (False, 'form')],
            'res_model': 'account.report.standard.ledger.line',
            'type': 'ir.actions.act_window',
            'domain': "[('report_id','=',%s),('type','not in',('5_super_total','4_total'))]" % (self.report_id.id),
            'context': {'search_default_%s' % self.type_ledger: 1, 'read_report_id': self.report_id.id},
            'target': 'current',
        }

    def print_pdf_report(self):
        self.ensure_one()
        self._compute_data()
        return self.env['report'].get_action(self, 'account_standard_report.report_account_standard_report')

    def print_excel_report(self):
        self.ensure_one()
        self._compute_data()
        return self.env['report'].get_action(self, 'account_standard_report.report_account_standard_excel')

    def _pre_compute(self):
        lang_code = self.env.context.get('lang') or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format
        time_format = self.env['res.lang']._lang_get(lang_code).time_format

        vals = {'report_name': self._get_name_report(),
                'name': self._get_name_report(),
                'print_time': '%s' % fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), datetime.now()).strftime(('%s %s') % (date_format, time_format)),
                'date_to': self.date_to if self.date_to else "2099-01-01",
                'date_from': self.date_from if self.date_from else "1970-01-01",
                }
        self.report_id = self.env['account.report.standard.ledger.report'].create(vals)
        self.account_ids = self._search_account()
        self.partner_ids = self._search_partner()

        if self.type_ledger in ('general', 'open'):
            self.type = 'account'
        elif self.type_ledger in ('partner', 'aged'):
            self.type = 'partner'
        else:
            self.type = 'journal'

        if self.type_ledger in ('partner', 'journal', 'open', 'aged'):
            self.compact_account = False
        if self.type_ledger not in ('partner', 'aged',):
            self.reconciled = True
            self.partner_select_ids = False

    def _compute_data(self):
        if not self.user_has_groups('account.group_account_user'):
            raise UserError(_('Your are not an accountant !'))
        self._pre_compute()

        self._sql_report_object()
        if self.type == 'account':
            self._sql_unaffected_earnings()
        if self.type in ('account, partner'):
            if self.type_ledger != 'aged':
                self._sql_init_balance()
        self._sql_lines()
        if self.compact_account and self.type_ledger == 'general':
            self._sql_lines_compacted()
        self._sql_total()
        self._sql_super_total()
        self.refresh()

        # complet total line
        line_obj = self.env['account.report.standard.ledger.line']
        self.report_id.line_total_ids = line_obj.search([('report_id', '=', self.report_id.id), ('type', '=', '4_total')])
        self.report_id.line_super_total_id = line_obj.search([('report_id', '=', self.report_id.id), ('type', '=', '5_super_total')], limit=1)
        self._format_total()

    def _sql_report_object(self):
        query = """INSERT INTO  account_report_standard_ledger_report_object
            (report_id, create_uid, create_date, object_id, name, account_id, partner_id, journal_id)
            SELECT DISTINCT
                %s AS report_id,
                %s AS create_uid,
                NOW() AS create_date,
                CASE
                    WHEN %s = 'account' THEN aml.account_id
                    WHEN %s = 'partner' THEN aml.partner_id
                    ELSE aml.journal_id
                END AS object_id,
                CASE
                    WHEN %s = 'account' THEN acc.code || ' ' || acc.name
                    WHEN %s = 'partner' THEN CASE WHEN rep.ref IS NULL THEN rep.name ELSE rep.ref || ' ' || rep.name END
                    ELSE acj.code || ' ' || acj.name
                END AS name,
                CASE WHEN %s = 'account' THEN aml.account_id ELSE NULL END AS account_id,
                CASE WHEN %s = 'partner' THEN aml.partner_id ELSE NULL END AS partner_id,
                CASE WHEN %s = 'journal' THEN aml.journal_id ELSE NULL END AS journal_id
            FROM
                account_move_line aml
                LEFT JOIN account_account acc ON (acc.id = aml.account_id)
                LEFT JOIN res_partner rep ON (rep.id = aml.partner_id)
                LEFT JOIN account_journal acj ON (acj.id = aml.journal_id)
            WHERE
                aml.company_id = %s
                AND aml.journal_id IN %s
                AND aml.account_id IN %s
                AND (%s in ('account', 'journal') OR aml.partner_id IN %s)
            ORDER BY
                name
            """

        params = [
            # SELECT
            self.report_id.id,
            self.env.uid,
            self.type, self.type, self.type, self.type,
            self.type, self.type, self.type,
            # WHERE
            self.company_id.id,
            tuple(self.journal_ids.ids) if self.journal_ids else (None,),
            tuple(self.account_ids.ids) if self.account_ids else (None,),
            self.type,
            tuple(self.partner_ids.ids) if self.partner_ids else (None,),
        ]
        self.env.cr.execute(query, tuple(params))

    def _sql_unaffected_earnings(self):
        company = self.company_id
        unaffected_earnings_account = self.env['account.account'].search([('company_id', '=', company.id), ('user_type_id', '=', self.env.ref('account.data_unaffected_earnings').id)], limit=1)
        if unaffected_earnings_account not in self.account_ids:
            return

        report_object_id = self.report_id.report_object_ids.filtered(lambda x: x.object_id == unaffected_earnings_account.id)
        if not report_object_id:
            report_object_id = self.report_id.report_object_ids.create({'report_id': self.report_id.id,
                                                                        'object_id': unaffected_earnings_account.id,
                                                                        'name': '%s %s' % (unaffected_earnings_account.code, unaffected_earnings_account.name),
                                                                        'account_id': unaffected_earnings_account.id})
        query = """
        INSERT INTO account_report_standard_ledger_line
            (report_id, create_uid, create_date, account_id, type, type_view, date, debit, credit, balance, cumul_balance, company_currency_id, reconciled, report_object_id)
        SELECT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
            %s AS account_id,
            '0_init' AS type,
            'init' AS type_view,
            %s AS date,
            CASE WHEN %s THEN COALESCE(SUM(aml.debit), 0) ELSE CASE WHEN COALESCE(SUM(aml.balance), 0) <= 0 THEN 0 ELSE COALESCE(SUM(aml.balance), 0) END END AS debit,
            CASE WHEN %s THEN COALESCE(SUM(aml.credit), 0) ELSE CASE WHEN COALESCE(SUM(aml.balance), 0) >= 0 THEN 0 ELSE COALESCE(-SUM(aml.balance), 0) END END AS credit,
            COALESCE(SUM(aml.balance), 0) AS balance,
            COALESCE(SUM(aml.balance), 0) AS cumul_balance,
            %s AS company_currency_id,
            FALSE as reconciled,
            %s AS report_object_id
        FROM
            account_move_line aml
            LEFT JOIN account_account acc ON (aml.account_id = acc.id)
            LEFT JOIN account_account_type acc_type ON (acc.user_type_id = acc_type.id)
            LEFT JOIN account_move m ON (aml.move_id = m.id)
        WHERE
            m.state IN %s
            AND aml.company_id = %s
            AND aml.date < %s
            AND acc_type.include_initial_balance = FALSE
        HAVING
            CASE
                WHEN %s = FALSE THEN ABS(SUM(aml.balance)) > %s
                ELSE ABS(SUM(aml.debit)) > %s OR ABS(SUM(aml.debit)) > %s OR ABS(SUM(aml.balance)) > %s
            END
        """

        date_from_fiscal = self.company_id.compute_fiscalyear_dates(datetime.strptime(self.report_id.date_from, DEFAULT_SERVER_DATE_FORMAT))['date_from']

        params = [
            # SELECT
            self.report_id.id,
            self.env.uid,
            unaffected_earnings_account.id,
            date_from_fiscal,
            self.init_balance_history,
            self.init_balance_history,
            self.company_currency_id.id,
            report_object_id.id,
            # WHERE
            ('posted',) if self.target_move == 'posted' else ('posted', 'draft',),
            company.id,
            self.report_id.date_from,
            # HAVING
            self.init_balance_history,
            self.company_currency_id.rounding, self.company_currency_id.rounding, self.company_currency_id.rounding, self.company_currency_id.rounding,
        ]

        self.env.cr.execute(query, tuple(params))

    def _sql_init_balance(self):
        company = self.company_id
        # initial balance partner
        query = """
        INSERT INTO account_report_standard_ledger_line
            (report_id, create_uid, create_date, account_id, partner_id, group_by_key, type, type_view, date, debit, credit, balance, cumul_balance, company_currency_id, reconciled, report_object_id)

        WITH matching_in_futur_before_init (id) AS
        (
        SELECT DISTINCT
            afr.id as id
        FROM
            account_full_reconcile afr
        INNER JOIN account_move_line aml ON aml.full_reconcile_id=afr.id
        WHERE
            aml.company_id = %s
            AND aml.date >= %s
        )
        SELECT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
            MIN(aml.account_id),
            CASE WHEN %s = 'partner' THEN MIN(aml.partner_id) ELSE NULL END,
            (CASE
                WHEN %s = 'account' THEN '-' || aml.account_id
                ELSE aml.partner_id || '-' || aml.account_id
            END) AS group_by_key,
            '0_init' AS type,
            'init' AS type_view,
            %s AS date,
            CASE WHEN %s THEN COALESCE(SUM(aml.debit), 0) ELSE CASE WHEN COALESCE(SUM(aml.balance), 0) <= 0 THEN 0 ELSE COALESCE(SUM(aml.balance), 0) END END AS debit,
            CASE WHEN %s THEN COALESCE(SUM(aml.credit), 0) ELSE CASE WHEN COALESCE(SUM(aml.balance), 0) >= 0 THEN 0 ELSE COALESCE(-SUM(aml.balance), 0) END END AS credit,
            COALESCE(SUM(aml.balance), 0) AS balance,
            COALESCE(SUM(aml.balance), 0) AS cumul_balance,
            %s AS company_currency_id,
            FALSE as reconciled,
            MIN(ro.id) AS report_object_id
        FROM
            account_report_standard_ledger_report_object ro
            INNER JOIN account_move_line aml ON (CASE WHEN %s = 'account' THEN aml.account_id = ro.object_id ELSE aml.partner_id = ro.object_id END)
            LEFT JOIN account_account acc ON (aml.account_id = acc.id)
            LEFT JOIN account_account_type acc_type ON (acc.user_type_id = acc_type.id)
            LEFT JOIN account_move m ON (aml.move_id = m.id)
            LEFT JOIN matching_in_futur_before_init mif ON (aml.full_reconcile_id = mif.id)
       	WHERE
            m.state IN %s
            AND ro.report_id = %s
            AND aml.company_id = %s
            AND aml.date < %s
            AND acc_type.include_initial_balance = TRUE
            AND aml.journal_id IN %s
            AND aml.account_id IN %s
            AND (%s in ('account', 'journal') OR aml.partner_id IN %s)
            AND ((%s AND acc.compacted = TRUE) OR acc.type_third_parties = 'no' OR (aml.full_reconcile_id IS NOT NULL AND mif.id IS NULL))
        GROUP BY
            group_by_key
        HAVING
            CASE
                WHEN %s = FALSE THEN ABS(SUM(aml.balance)) > %s
                ELSE ABS(SUM(aml.debit)) > %s OR ABS(SUM(aml.debit)) > %s OR ABS(SUM(aml.balance)) > %s
            END
        """

        params = [
            # matching_in_futur
            company.id,
            self.report_id.date_from,

            # init_account_table
            # SELECT
            self.report_id.id,
            self.env.uid,
            self.type, self.type,
            self.report_id.date_from,
            self.init_balance_history,
            self.init_balance_history,
            self.company_currency_id.id,
            # FROM
            self.type,
            # WHERE
            ('posted',) if self.target_move == 'posted' else ('posted', 'draft',),
            self.report_id.id,
            company.id,
            self.report_id.date_from,
            tuple(self.journal_ids.ids) if self.journal_ids else (None,),
            tuple(self.account_ids.ids) if self.account_ids else (None,),
            self.type,
            tuple(self.partner_ids.ids) if self.partner_ids else (None,),
            self.compact_account,

            # HAVING
            self.init_balance_history,
            self.company_currency_id.rounding, self.company_currency_id.rounding, self.company_currency_id.rounding, self.company_currency_id.rounding,
        ]

        self.env.cr.execute(query, tuple(params))

    def _sql_lines(self):
        # lines_table
        query = """
        INSERT INTO account_report_standard_ledger_line
            (report_id, create_uid, create_date, account_id, type, type_view, journal_id, partner_id, move_id, move_line_id, date, date_maturity, debit, credit, balance, full_reconcile_id, reconciled, report_object_id, cumul_balance, current, age_30_days, age_60_days, age_90_days, age_120_days, older, company_currency_id)

        WITH matching_in_futur_before_init (id) AS
        (
            SELECT DISTINCT
                afr.id AS id
            FROM
                account_full_reconcile afr
            INNER JOIN account_move_line aml ON aml.full_reconcile_id=afr.id
            WHERE
                aml.company_id = %s
                AND aml.date >= %s
        ),

        matching_in_futur_after_date_to (id) AS
        (
            SELECT DISTINCT
                afr.id AS id
            FROM
                account_full_reconcile afr
                INNER JOIN account_move_line aml ON aml.full_reconcile_id = afr.id
            WHERE
                aml.company_id = %s
                AND aml.date > %s
        ),

        initial_balance (id, balance) AS
        (
            SELECT
                MIN(report_object_id) AS id,
                COALESCE(SUM(balance), 0) AS balance
            FROM
                account_report_standard_ledger_line
            WHERE
                report_id = %s
                AND type = '0_init'
            GROUP BY
                report_object_id
        ),

        date_range AS
            (
                SELECT
                    %s AS date_current,
                    DATE %s - INTEGER '30' AS date_less_30_days,
                    DATE %s - INTEGER '60' AS date_less_60_days,
                    DATE %s - INTEGER '90' AS date_less_90_days,
                    DATE %s - INTEGER '120' AS date_less_120_days,
                    DATE %s - INTEGER '150' AS date_older
            )

        SELECT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
            aml.account_id,
            CASE WHEN aml.date >= %s THEN '2_line' ELSE '1_init_line' END AS type,
            CASE WHEN aml.date >= %s THEN 'normal' ELSE 'init' END AS type_view,
            aml.journal_id,
            aml.partner_id,
            aml.move_id,
            aml.id,
            aml.date,
            aml.date_maturity,
            aml.debit,
            aml.credit,
            aml.balance,
            aml.full_reconcile_id,
            CASE WHEN aml.full_reconcile_id is NOT NULL AND NOT mifad.id IS NOT NULL THEN TRUE ELSE FALSE END AS reconciled,
            ro.id AS report_object_id,
            CASE
                WHEN %s = 'account' THEN COALESCE(init.balance, 0) + (SUM(aml.balance) OVER (PARTITION BY aml.account_id ORDER BY aml.account_id, aml.date, aml.id))
                WHEN %s = 'partner' THEN COALESCE(init.balance, 0) + (SUM(aml.balance) OVER (PARTITION BY aml.partner_id ORDER BY aml.partner_id, aml.date, aml.id))
                ELSE SUM(aml.balance) OVER (PARTITION BY aml.journal_id ORDER BY aml.journal_id, aml.date, aml.id)
            END AS cumul_balance,
            CASE WHEN aml.date_maturity > date_range.date_less_30_days THEN aml.balance END AS current,
            CASE WHEN aml.date_maturity > date_range.date_less_60_days AND aml.date_maturity <= date_range.date_less_30_days THEN aml.balance END AS age_30_days,
            CASE WHEN aml.date_maturity > date_range.date_less_90_days AND aml.date_maturity <= date_range.date_less_60_days THEN aml.balance END AS age_60_days,
            CASE WHEN aml.date_maturity > date_range.date_less_120_days AND aml.date_maturity <= date_range.date_less_90_days THEN aml.balance END AS age_90_days,
            CASE WHEN aml.date_maturity > date_range.date_older AND aml.date_maturity <= date_range.date_less_120_days THEN aml.balance END AS age_120_days,
            CASE WHEN aml.date_maturity <= date_range.date_older THEN aml.balance END AS older,
            %s AS company_currency_id
        FROM
            date_range,
            account_report_standard_ledger_report_object ro
            INNER JOIN account_move_line aml ON (
                CASE
                    WHEN %s = 'account' THEN aml.account_id = ro.object_id
                    WHEN %s = 'partner' THEN aml.partner_id = ro.object_id
                    ELSE aml.journal_id = ro.object_id
                END)
            LEFT JOIN account_journal j ON (aml.journal_id = j.id)
            LEFT JOIN account_account acc ON (aml.account_id = acc.id)
            LEFT JOIN account_account_type acc_type ON (acc.user_type_id = acc_type.id)
            LEFT JOIN account_move m ON (aml.move_id = m.id)
            LEFT JOIN matching_in_futur_before_init mif ON (aml.full_reconcile_id = mif.id)
            LEFT JOIN matching_in_futur_after_date_to mifad ON (aml.full_reconcile_id = mifad.id)
            LEFT JOIN initial_balance init ON (ro.id = init.id)
        WHERE
            m.state IN %s
            AND ro.report_id = %s
            AND aml.company_id = %s
            AND (CASE
                    WHEN %s = 'journal' THEN aml.date >= %s
                    WHEN aml.date >= %s THEN %s != 'open'
                    ELSE acc.type_third_parties IN ('supplier', 'customer') AND (aml.full_reconcile_id IS NULL OR mif.id IS NOT NULL)
                END)
            AND aml.date <= %s
            AND aml.journal_id IN %s
            AND aml.account_id IN %s
            AND (%s IN ('account','journal') OR aml.partner_id IN %s)
            AND NOT (%s AND acc.compacted = TRUE)
            AND (%s OR NOT (aml.full_reconcile_id is NOT NULL AND NOT mifad.id IS NOT NULL))
        ORDER BY
            aml.date, aml.id
        """
        params = [
            # matching_in_futur init
            self.company_id.id,

            self.report_id.date_from,

            # matching_in_futur date_to
            self.company_id.id,
            self.report_id.date_to,

            # initial_balance
            self.report_id.id,

            # date_range
            self.report_id.date_to, self.report_id.date_to, self.report_id.date_to, self.report_id.date_to, self.report_id.date_to, self.report_id.date_to,

            # lines_table
            # SELECT
            self.report_id.id,
            self.env.uid,
            self.report_id.date_from,
            self.report_id.date_from,
            self.type, self.type,
            self.company_currency_id.id,

            # FROM
            self.type, self.type,

            # WHERE
            ('posted',) if self.target_move == 'posted' else ('posted', 'draft',),
            self.report_id.id,
            self.company_id.id,

            self.type, self.report_id.date_from,
            self.report_id.date_from, self.type_ledger,
            self.report_id.date_to,
            tuple(self.journal_ids.ids) if self.journal_ids else (None,),
            tuple(self.account_ids.ids) if self.account_ids else (None,),
            self.type,
            tuple(self.partner_ids.ids) if self.partner_ids else (None,),
            self.compact_account,
            self.reconciled,

        ]

        self.env.cr.execute(query, tuple(params))

    def _sql_lines_compacted(self):
        query = """
        INSERT INTO account_report_standard_ledger_line
            (report_id, create_uid, create_date, account_id, type, type_view, date, debit, credit, balance, cumul_balance, company_currency_id, report_object_id)

        WITH initial_balance (id, balance) AS
        (
        SELECT
            MIN(report_object_id) AS id,
            COALESCE(SUM(balance), 0) AS balance
        FROM
            account_report_standard_ledger_line
        WHERE
            report_id = %s
            AND type = '0_init'
        GROUP BY
            report_object_id
        )

        SELECT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
            MIN(aml.account_id) AS account_id,
            '3_compact' AS type,
            'normal' AS type_view,
            %s AS date,
            COALESCE(SUM(aml.debit), 0) AS debit,
            COALESCE(SUM(aml.credit), 0) AS credit,
            COALESCE(SUM(aml.balance), 0) AS balance,
            COALESCE(MIN(init.balance), 0) + COALESCE(SUM(aml.balance), 0) AS cumul_balance,
            %s AS company_currency_id,
            MIN(ro.id) AS report_object_id
        FROM
            account_report_standard_ledger_report_object ro
            INNER JOIN account_move_line aml ON (aml.account_id = ro.object_id)
            LEFT JOIN account_journal j ON (aml.journal_id = j.id)
            LEFT JOIN account_account acc ON (aml.account_id = acc.id)
            LEFT JOIN account_account_type acc_type ON (acc.user_type_id = acc_type.id)
            LEFT JOIN account_move m ON (aml.move_id = m.id)
            LEFT JOIN initial_balance init ON (ro.id = init.id)
        WHERE
            m.state IN %s
            AND ro.report_id = %s
            AND aml.company_id = %s
            AND aml.date >= %s
            AND aml.date <= %s
            AND aml.journal_id IN %s
            AND aml.account_id IN %s
            AND (%s AND acc.compacted = TRUE)
        GROUP BY
            aml.account_id
        """

        params = [
            # initial_balance
            self.report_id.id,

            # SELECT
            self.report_id.id,
            self.env.uid,
            self.report_id.date_from,
            self.company_currency_id.id,
            # FROM

            # WHERE
            ('posted',) if self.target_move == 'posted' else ('posted', 'draft',),
            self.report_id.id,
            self.company_id.id,
            self.report_id.date_from,
            self.report_id.date_to,
            tuple(self.journal_ids.ids) if self.journal_ids else (None,),
            tuple(self.account_ids.ids) if self.account_ids else (None,),
            self.compact_account,
        ]

        self.env.cr.execute(query, tuple(params))

    def _sql_total(self):
        query = """
        INSERT INTO account_report_standard_ledger_line
            (report_id, create_uid, create_date, account_id, partner_id, journal_id, type, type_view, date, debit, credit, balance, cumul_balance, report_object_id, current, age_30_days, age_60_days, age_90_days, age_120_days, older, company_currency_id)
        SELECT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
            CASE WHEN %s = 'account' THEN MIN(account_id) ELSE NULL END AS account_id,
            CASE WHEN %s = 'partner' THEN MIN(partner_id) ELSE NULL END AS partner_id,
            CASE WHEN %s = 'journal' THEN MIN(journal_id) ELSE NULL END AS journal_id,
            '4_total' AS type,
            'total' AS type_view,
            %s AS date,
            COALESCE(SUM(debit), 0) AS debit,
            COALESCE(SUM(credit), 0) AS credit,
            COALESCE(SUM(balance), 0) AS balance,
            COALESCE(SUM(balance), 0) AS cumul_balance,
            MIN(report_object_id) AS report_object_id,
            COALESCE(SUM(current), 0) AS current,
            COALESCE(SUM(age_30_days), 0) AS age_30_days,
            COALESCE(SUM(age_60_days), 0) AS age_60_days,
            COALESCE(SUM(age_90_days), 0) AS age_90_days,
            COALESCE(SUM(age_120_days), 0) AS age_120_days,
            COALESCE(SUM(older), 0) AS older,
            %s AS company_currency_id
        FROM
            account_report_standard_ledger_line
        WHERE
            report_id = %s
            AND report_object_id IS NOT NULL
        GROUP BY
            report_object_id
        ORDER BY
            report_object_id
        """
        params = [
            # SELECT
            self.report_id.id,
            self.env.uid,
            self.type, self.type, self.type,
            self.report_id.date_from,
            self.company_currency_id.id,

            # WHERE
            self.report_id.id,

        ]
        self.env.cr.execute(query, tuple(params))

    def _sql_super_total(self):
        query = """
        INSERT INTO account_report_standard_ledger_line
            (report_id, create_uid, create_date, type, type_view, date, debit, credit, balance, cumul_balance, current, age_30_days, age_60_days, age_90_days, age_120_days, older, company_currency_id)
        SELECT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
            '5_super_total' AS type,
            'total' AS type_view,
            %s AS date,
            COALESCE(SUM(debit), 0) AS debit,
            COALESCE(SUM(credit), 0) AS credit,
            COALESCE(SUM(balance), 0) AS balance,
            COALESCE(SUM(balance), 0) AS cumul_balance,
            COALESCE(SUM(current), 0) AS current,
            COALESCE(SUM(age_30_days), 0) AS age_30_days,
            COALESCE(SUM(age_60_days), 0) AS age_60_days,
            COALESCE(SUM(age_90_days), 0) AS age_90_days,
            COALESCE(SUM(age_120_days), 0) AS age_120_days,
            COALESCE(SUM(older), 0) AS older,
            %s AS company_currency_id
        FROM
            account_report_standard_ledger_line
        WHERE
            report_id = %s
            AND type = '4_total'
        """
        params = [
            # SELECT
            self.report_id.id,
            self.env.uid,
            self.report_id.date_from,
            self.company_currency_id.id,
            self.report_id.id,
        ]
        self.env.cr.execute(query, tuple(params))

    def _search_account(self):
        type_ledger = self.type_ledger
        domain = [('deprecated', '=', False), ('company_id', '=', self.company_id.id)]
        if type_ledger in ('partner', 'aged',):
            result_selection = self.result_selection
            if result_selection == 'supplier':
                acc_type = ('supplier',)
            elif result_selection == 'customer':
                acc_type = ('customer',)
            else:
                acc_type = ('supplier', 'customer',)
            domain.append(('type_third_parties', 'in', acc_type))

        account_in_ex_clude = self.account_in_ex_clude.ids
        acc_methode = self.account_methode
        if account_in_ex_clude:
            if acc_methode == 'include':
                domain.append(('id', 'in', account_in_ex_clude))
            elif acc_methode == 'exclude':
                domain.append(('id', 'not in', account_in_ex_clude))
        return self.env['account.account'].search(domain)

    def _search_partner(self):
        if self.type_ledger in ('partner', 'aged'):
            if self.partner_select_ids:
                return self.partner_select_ids
            return self.env['res.partner'].search([])
        return False

    def _get_name_report(self):
        report_name = D_LEDGER[self.type_ledger]['name']
        if self.summary:
            report_name += _(' Balance')
        return report_name

    def _sql_get_line_for_report(self, type_l, report_object=None):
        query = """SELECT
                    aml.report_object_id AS report_object_id,
                    aml.type_view AS type_view,
                    CASE
                        WHEN %s = 'account' THEN acc.code
                        WHEN %s = 'journal' THEN acj.code
                        ELSE rep.ref
                    END AS code,
                    CASE
                        WHEN %s = 'account' THEN acc.name
                        WHEN %s = 'journal' THEN acj.name
                        ELSE rep.name
                    END AS name,
                    acj.code AS j_code,
                    acc.code AS a_code,
                    acc.name AS a_name,
                    aml.current AS current,
                    aml.age_30_days AS age_30_days,
                    aml.age_60_days AS age_60_days,
                    aml.age_90_days AS age_90_days,
                    aml.age_120_days AS age_120_days,
                    aml.older AS older,
                    aml.credit AS credit,
                    aml.debit AS debit,
                    aml.cumul_balance AS cumul_balance,
                    aml.balance AS balance,
                    ml.name AS move_name,
                    ml.ref AS displayed_name,
                    rep.name AS partner_name,
                    aml.date AS date,
                    aml.date_maturity AS date_maturity,
                    CASE
                        WHEN aml.full_reconcile_id IS NOT NULL THEN (CASE WHEN aml.reconciled = TRUE THEN afr.name ELSE '*' END)
                        ELSE ''
                    END AS matching_number
                FROM
                    account_report_standard_ledger_line aml
                    LEFT JOIN account_account acc ON (acc.id = aml.account_id)
                    LEFT JOIN account_journal acj ON (acj.id = aml.journal_id)
                    LEFT JOIN res_partner rep ON (rep.id = aml.partner_id)
                    LEFT JOIN account_move ml ON (ml.id = aml.move_id)
                    LEFT JOIN account_full_reconcile afr ON (aml.full_reconcile_id = afr.id)
                WHERE
                    aml.report_id = %s
                    AND (%s OR aml.report_object_id = %s)
                    AND aml.type IN %s
                ORDER BY
                    aml.id
                """
        params = [
            self.type, self.type, self.type, self.type,
            self.report_id.id,
            True if report_object is None else False,
            report_object,
            type_l
        ]

        self.env.cr.execute(query, tuple(params))
        return self.env.cr.dictfetchall()

    def _format_total(self):
        if not self.company_currency_id:
            return
        lines = self.report_id.line_total_ids + self.report_id.line_super_total_id
        for line in lines:
            line.write({
                'debit': self.company_currency_id.round(line.debit) + 0.0,
                'credit': self.company_currency_id.round(line.credit) + 0.0,
                'balance': self.company_currency_id.round(line.balance) + 0.0,
                'current': self.company_currency_id.round(line.current) + 0.0,
                'age_30_days': self.company_currency_id.round(line.age_30_days) + 0.0,
                'age_60_days': self.company_currency_id.round(line.age_60_days) + 0.0,
                'age_90_days': self.company_currency_id.round(line.age_90_days) + 0.0,
                'age_120_days': self.company_currency_id.round(line.age_120_days) + 0.0,
                'older': self.company_currency_id.round(line.older) + 0.0,
            })
