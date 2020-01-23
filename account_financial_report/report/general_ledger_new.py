
# © 2016 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import operator
import itertools
from odoo import models, fields, api, _


class GeneralLedgerReport(models.AbstractModel):
    _name = 'report.account_financial_report.general_ledger'

    def _get_unaffected_earnings_account(self, company):
        account_type = self.env.ref('account.data_unaffected_earnings')
        return self.env['account.account'].search(
            [
                ('user_type_id', '=', account_type.id),
                ('company_id', '=', company.id)
            ], limit=1).id

    def _get_move_lines_read_group_domain(self, data, company):
        domain = [('account_id', '!=', self._get_unaffected_earnings_account(company))]
        if data['account_ids']:
            domain += [('account_id', 'in', data['account_ids'])]
        if data['partner_ids']:
            domain += [('partner_id', 'in', data['partner_ids'])]
        if data['analytic_tag_ids']:
            domain += [('analytic_tag_ids', 'in', data['analytic_tag_ids'])]
        domain += [('date', '<=', data['date_to'])]
        return domain

    def _get_account_id_data(self, account_id):
        account = self.env['account.account'].browse(account_id)
        return {
            'name': account.name,
            'code': account.code,
            'internal_type': account.internal_type,
            'is_partner_account': account.internal_type in ['receivable', 'payable'],
            'currency_id': account.currency_id.id,
        }

    def _get_partner_accounts(self, wiz, data, company):
        partner_account_ids = self.env['account.move.line'].read_group(
            self._get_move_lines_read_group_domain(data, company), ['account_id', 'partner_id'], ['account_id', 'partner_id'], lazy=False
        )
        account_data = {}
        account_ids = []
        partner_ids = set()
        for account_partner in partner_account_ids:
            print(account_partner)
            if not account_data.get(account_partner['account_id'][0], False):
                account_data[account_partner['account_id'][0]] = self._get_account_id_data(account_partner['account_id'][0])
                account_ids.append(account_partner['account_id'][0])
                account_data[account_partner['account_id'][0]]['partners'] = {}
            if account_partner['partner_id']:
                account_data[account_partner['account_id'][0]]['partners'][account_partner['partner_id'][0]] = {}
                partner_ids.add(account_partner['partner_id'][0])
        return account_data, account_ids, list(partner_ids)

    def _get_move_lines_domain(self, account_ids, partner_ids, data):
        return [
            ('account_id', 'in', account_ids),
            ('partner_id', 'in', partner_ids + [False]),
            ('date', '<=', data['date_to']),
        ]

    def _get_move_lines_order(self):
            return 'account_id, partner_id, date'

    def _get_move_lines_data(self, ml):
            return {
                'move_line_id': ml.id,
                'date': ml.date,
                'journal_id': ml.journal_id.id,
                'account_id': ml.account_id.id,
                'partner_id': ml.partner_id.id,
                'label': ml.name,
                'debit': ml.debit,
                'credit': ml.credit,
                'company_currency_id': ml.company_currency_id.id,
                'amount_currency': ml.amount_currency,
                'currency_id': ml.currency_id.id,
                'tax_line_id': ml.tax_line_id.id,
                'base_debit': ml.debit,
                'base_credit': ml.credit,
                'base_balance': ml.balance,
            }

    def _get_move_lines(self, data, account_ids, partner_ids):
        move_lines = self.env['account.move.line'].search(
            self._get_move_lines_domain(account_ids, partner_ids, data),
            order=self._get_move_lines_order())
        move_lines_data = []
        for ml in move_lines:
            move_lines_data.append(self._get_move_lines_data(ml))
        return move_lines_data

    @api.multi
    def _get_report_values(self, docids, data):
        wizard_id = data['wizard_id']
        wizard = self.env['general.ledger.report.wizard'].browse(wizard_id)
        company = self.env['res.company'].browse(data['company_id'])

        account_data, account_ids, partner_ids = self._get_partner_accounts(
            wizard, data, company)
        move_line_ids_data = self._get_move_lines(data, account_ids, partner_ids)
        # Add all move lines to account,partner pair related lists.
        for key_acc, items_acc in itertools.groupby(
            move_line_ids_data, operator.itemgetter('account_id')):
            for key_par, items_par in itertools.groupby(
                items_acc, operator.itemgetter('partner_id')
            ):
                if key_par:
                    account_data[key_acc]['partners'][key_par]['move_lines'] = list(items_par)
                else:
                    account_data[key_acc]['partners']['no_partner'] = {}
                    account_data[key_acc]['partners']['no_partner']['move_lines'] = list(items_par)
        # Fill headers for account or partners
        # TODO:
        for account_id in account_ids:
            if account_data[account_id]['is_partner_account']:
                for partner_id in account_data[account_id]['partners']:

