# -*- coding: utf-8 -*-
# © 2015 Yannick Vaucher (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class FinancialReportLine(models.Model):
    _inherit = 'financial.report.line'
    _name = 'general.ledger.line'
    _description = "General Ledger report line"

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
