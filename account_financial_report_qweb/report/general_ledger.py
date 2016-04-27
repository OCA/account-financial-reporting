# -*- coding: utf-8 -*-
# © 2015 Yannick Vaucher (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api
from openerp import tools


class FinancialReportLine(models.Model):
    _inherit = 'financial.report.line'
    _name = 'general.ledger.line'
    _description = "General Ledger report"

    _auto = False
    _order = 'account_id, date'

    @api.depends('invoice_number', 'name')
    def _get_label(self):
        for rec in self:
            label = rec.name
            if rec.invoice_number:
                label += u' ({})'.format(rec.invoice_number)
            rec.label = label

    label = fields.Char(compute='_get_label', readonly=True, store=False)

    def init(self, cr):
        report_name = self._name.replace('.', '_')
        tools.drop_view_if_exists(cr, report_name)
        query = """
CREATE OR REPLACE VIEW %(report_name)s AS (
  SELECT
    acc.id AS account_id,
    acc.code AS account_code,
    acc.centralized,
    ml.id,
    ml.name,
    ml.ref,
    ml.date,
    date_part('year', ml.date) || '-' || date_part('month', ml.date)
        AS month,
    part.ref AS partner_ref,
    part.name AS partner_name,
    ml.journal_id,
    ml.currency_id,
    cur.name AS currency_code,
    ml.debit,
    ml.credit,
    ml.debit - ml.credit AS balance,
    ml.amount_currency,

    SUM(amount_currency) OVER w_account AS balance_curr,
    SUM(debit) OVER w_account AS cumul_debit,
    SUM(credit) OVER w_account AS cumul_credit,
    SUM(debit - credit) OVER w_account AS cumul_balance,
    SUM(amount_currency) OVER w_account AS cumul_balance_curr,

    SUM(debit) OVER w_account - debit AS init_debit,
    SUM(credit) OVER w_account - credit AS init_credit,
    SUM(debit - credit) OVER w_account - (debit - credit) AS init_balance,
    SUM(amount_currency) OVER w_account - (amount_currency)
        AS init_balance_curr,

    SUM(debit) OVER w_account_centralized AS debit_centralized,
    SUM(credit) OVER w_account_centralized AS credit_centralized,
    SUM(debit - credit) OVER w_account_centralized AS balance_centralized,
    SUM(amount_currency) OVER w_account_centralized
        AS balance_curr_centralized,

    SUM(debit) OVER w_account - SUM(debit)
        OVER w_account_centralized AS init_debit_centralized,
    SUM(credit) OVER w_account - SUM(credit)
        OVER w_account_centralized AS init_credit_centralized,
    SUM(debit - credit) OVER w_account - SUM(debit - credit)
        OVER w_account_centralized AS init_balance_centralized,
    SUM(amount_currency) OVER w_account - SUM(amount_currency)
        OVER w_account_centralized AS init_balance_curr_centralized,

    m.name AS move_name,
    m.state AS move_state,
    i.number AS invoice_number
  FROM
    account_account AS acc
    LEFT JOIN account_move_line AS ml ON (ml.account_id = acc.id)
    INNER JOIN res_partner AS part ON (ml.partner_id = part.id)
    INNER JOIN account_move AS m ON (ml.move_id = m.id)
    LEFT JOIN account_invoice AS i ON (m.id = i.move_id)
    LEFT JOIN res_currency AS cur ON (ml.currency_id = cur.id)
  WINDOW w_account AS (PARTITION BY acc.code ORDER BY ml.date, ml.id),
         w_account_centralized AS (
           PARTITION BY acc.code,
                        date_part('year', ml.date),
                        date_part('month', ml.date),
                        ml.journal_id,
                        ml.partner_id
           ORDER BY ml.date, ml.journal_id, ml.id)
)
        """ % {'report_name': report_name}
        cr.execute(query)


class GeneralLedgerReport(models.TransientModel):

    _name = 'report.account.report_generalledger_qweb'
    _inherit = 'account.report.common'

    @api.multi
    def _get_account_ids(self):
        res = False
        context = self.env.context
        if (context.get('active_model') == 'account.account' and
                context.get('active_ids')):
            res = context['active_ids']
        return res

    name = fields.Char()
    initial_balance = fields.Integer()
    account_ids = fields.Many2many(
        'account.account',
        string='Filter on accounts',
        default=_get_account_ids,
        help="Only selected accounts will be printed. Leave empty to "
             "print all accounts.")
    journal_ids = fields.Many2many(
        'account.journal',
        string='Filter on jourvals',
        help="Only selected journals will be printed. Leave empty to "
             "print all journals.")
    balance_mode = fields.Selection(
        [('initial_balance', 'Initial balance'),
         ('opening_balance', 'Opening balance')]
    )
    display_account = fields.Char()
    display_ledger_lines = fields.Boolean()
    display_initial_balance = fields.Boolean()

    MAPPING = {
        'date_from': 'start_date',
        'date_to': 'end_date',
    }

    @api.model
    def _get_values_from_wizard(self, data):
        """ Get values from wizard """
        values = {}
        for key, val in data.iteritems():
            if key in self.MAPPING:
                values[self.MAPPING[key]] = val
            elif key == 'fiscalyear':
                if val:
                    values[key] = val[0]
            elif key == 'journal_ids':
                if val:
                    values[key] = [(6, 0, val)]
            else:
                values[key] = val
        return values

    @api.multi
    def _get_centralized_move_ids(self, domain):
        """ Get last line of each selected centralized accounts """
        # inverse search on centralized boolean to finish the search to get the
        # ids of last lines of centralized accounts
        # XXX USE DISTINCT to speed up ?
        domain = domain[:]
        centralize_index = domain.index(('centralized', '=', False))
        domain[centralize_index] = ('centralized', '=', True)

        gl_lines = self.env['general.ledger.line'].search(domain)
        accounts = gl_lines.mapped('account_id')

        line_ids = []
        for acc in accounts:
            acc_lines = gl_lines.filtered(lambda rec: rec.account_id == acc)
            line_ids.append(acc_lines[-1].id)
        return line_ids

    @api.multi
    def _get_moves_from_dates(self):
        domain = self._get_moves_from_dates_domain()
        if self.centralize:
            centralized_ids = self._get_centralized_move_ids(domain)
            if centralized_ids:
                domain.insert(0, '|')
                domain.append(('id', 'in', centralized_ids))
        return self.env['general.ledger.line'].search(domain)

    @api.multi
    def render_html(self, data=None):
        report_name = 'account.report_generalledger_qweb'
        if data is None:
            return
        values = self._get_values_from_wizard(data['form'])
        report = self.create(values)

        report_lines = report._get_moves_from_dates()
        # TODO warning if no report_lines
        self.env['report']._get_report_from_name(report_name)

        docargs = {
            'doc_ids': report.ids,
            'doc_model': self._name,
            'report_lines': report_lines,
            'docs': report,
            # XXX
            'has_currency': True
        }
        return self.env['report'].render(report_name, docargs)
