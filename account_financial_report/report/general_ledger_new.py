
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
                if account_data[account_partner['account_id'][0]]['is_partner_account']:
                    account_data[account_partner['account_id'][0]]['partners'] = {}
            if account_partner['partner_id'] and account_data[account_partner['account_id'][0]]['is_partner_account']:
                account_data[account_partner['account_id'][0]]['partners'][account_partner['partner_id'][0]] = {}
                partner_ids.add(account_partner['partner_id'][0])
            elif not account_partner['partner_id'] and account_data[account_partner['account_id'][0]]['is_partner_account']\
                and account_data[account_partner['account_id'][0]]['partners'].get(0, False):
                account_data[account_partner['account_id'][0]]['partners'][0] = {}
                account_data[account_partner['account_id'][0]]['partner_account_with_empty_partners'] = True
            if not account_partner['partner_id'] and not account_data[account_partner['account_id'][0]].get('move_lines', False):
                account_data[account_partner['account_id'][0]]['move_lines'] = {}
        return account_data, account_ids, list(partner_ids)

    def _get_move_lines_domain(self, account_ids, partner_ids, date_from, date_to):
        domain = [
            ('account_id', 'in', account_ids),
            ('partner_id', 'in', partner_ids + [False]),
        ]
        if date_from:
            domain += [('date', '>=', date_from)]
        if date_to:
            domain += [('date', '<=', date_to)]
        return domain

    def _get_move_lines_order(self):
            return 'account_id, partner_id, date'

    def _get_move_lines_data(self, ml):
            return {
                'move_line_id': ml.id,
                'date': ml.date,
                'journal_name': ml.journal_id.name,
                'account_id': ml.account_id.id,
                'account_code': ml.account_id.code,
                'partner_name': ml.partner_id.display_name,
                'partner_id': ml.partner_id.id,
                'label': ml.name,
                'debit': ml.debit,
                'credit': ml.credit,
                'company_currency_id': ml.company_currency_id.id,
                'amount_currency': ml.amount_currency,
                'currency_id': ml.currency_id.id,
                'tax_line_name': ml.tax_line_id.name,
                'base_debit': ml.debit,
                'base_credit': ml.credit,
                'base_balance': ml.balance,
            }

    def _get_move_lines(self, account_ids, partner_ids, date_from=None, date_to=None):
        move_lines = self.env['account.move.line'].search(
            self._get_move_lines_domain(account_ids, partner_ids, date_from, date_to),
            order=self._get_move_lines_order())
        move_lines_data = []
        for ml in move_lines:
            move_lines_data.append(self._get_move_lines_data(ml))
        return move_lines_data

    def _update_partner_account_header(self, account_data, date_to=None):
        for account in account_data:
            if account_data[account]['is_partner_account']:
                for partner in account_data[account]['partners']:
                    initial_debit_balance = initial_credit_balance = initial_cumul_balance = 0.0
                    move_line_data = self._get_move_lines([account,], [partner,], date_to=date_to)
                    if move_line_data:
                        initial_debit_balance = sum([x['base_debit'] for x in move_line_data])
                        initial_credit_balance = sum([x['base_credit'] for x in move_line_data])
                        initial_cumul_balance = initial_debit_balance - initial_credit_balance
                    account_data[account]['partners'][partner]['init_header'] = \
                        {
                            'initial_debit_balance': initial_debit_balance,
                            'initial_credit_balance': initial_credit_balance,
                            'initial_cumul_balance': initial_cumul_balance,
                        }
                if account_data[account].get('partner_account_with_empty_partners', False):
                    initial_debit_balance = initial_credit_balance = initial_cumul_balance = 0.0
                    move_line_data = self._get_move_lines([account,], [False,], date_to=date_to)
                    if move_line_data:
                        initial_debit_balance = sum([x['base_debit'] for x in move_line_data])
                        initial_credit_balance = sum([x['base_credit'] for x in move_line_data])
                        initial_cumul_balance = initial_debit_balance - initial_credit_balance
                    account_data[account]['partners'][False]['init_header'] = \
                        {
                            'initial_debit_balance': initial_debit_balance,
                            'initial_credit_balance': initial_credit_balance,
                            'initial_cumul_balance': initial_cumul_balance,
                        }
            else:
                initial_debit_balance = 0.0
                initial_credit_balance = 0.0
                initial_cumul_balance = 0.0
                move_line_data = self._get_move_lines([account,], [partner for partner in account_data[account]['partners']] if account_data[account].get('partners', False) else [], date_to=date_to)
                if move_line_data:
                    initial_debit_balance = sum(
                        [x['base_debit'] for x in move_line_data])
                    initial_credit_balance = sum(
                        [x['base_credit'] for x in move_line_data])
                    initial_cumul_balance = initial_debit_balance - initial_credit_balance
                account_data[account]['init_header'] = \
                    {
                        'initial_debit_balance': initial_debit_balance,
                        'initial_credit_balance': initial_credit_balance,
                        'initial_cumul_balance': initial_cumul_balance,
                    }
        return account_data


    @api.multi
    def _get_report_values(self, docids, data):
        date_to = data['date_to']
        date_from = data['date_from']
        wizard_id = data['wizard_id']
        wizard = self.env['general.ledger.report.wizard'].browse(wizard_id)
        company = self.env['res.company'].browse(data['company_id'])

        account_data, account_ids, partner_ids = self._get_partner_accounts(
            wizard, data, company)
        # Fill Headers to Partners/Accounts
        account_data = self._update_partner_account_header(account_data, date_to=date_from)
        # Get Move Lines Data
        move_line_ids_data = self._get_move_lines(account_ids, partner_ids, date_from=date_from, date_to=date_to)
        # Add all move lines to account,partner pair related lists.
        for key_acc, items_acc in itertools.groupby(
            move_line_ids_data, operator.itemgetter('account_id')):
            if account_data[key_acc]['is_partner_account']:
                for key_par, items_par in itertools.groupby(
                    items_acc, operator.itemgetter('partner_id')
                ):
                    if key_par:
                        account_data[key_acc]['partners'][key_par]['move_lines'] = list(items_par)
                    else:
                        account_data[key_acc]['partners'][0]['move_lines'] = list(items_par)
            else:
                account_data[key_acc]['move_lines'] = list(items_acc)
        for account in account_ids:
            if account_data[account]['is_partner_account']:
                final_debit = 0.0
                final_credit = 0.0
                final_cumul_balance = 0.0
                if account_data[account].get('partners', False):
                    for partner_id in account_data[account]['partners']:
                        init_header = account_data[account]['partners'][partner_id]['init_header']
                        final_partner_debit = init_header['initial_debit_balance']
                        final_partner_credit = init_header['initial_credit_balance']
                        previous_partner_cumul_balance = init_header['initial_cumul_balance']
                        for key, move_line in account_data[account]['partners'][partner_id].items():
                            account_data[account]['partners'][partner_id][key]['cumul_balance'] += previous_partner_cumul_balance
                            previous_partner_cumul_balance = account_data[account]['partners'][partner_id][key]['cumul_balance']
                            final_partner_debit += account_data[account]['partners'][partner_id][key]['initial_debit_balance']
                            final_partner_credit += account_data[account]['partners'][partner_id][key]['initial_credit_balance']
                        account_data[account]['partners'][partner_id]['final_header'] = {
                            'final_partner_debit': final_partner_debit,
                            'final_partner_credit': final_partner_credit,
                            'final_cumul_balance': previous_partner_cumul_balance
                        }
                        final_debit += final_partner_debit
                        final_credit += final_partner_credit
                        final_cumul_balance += previous_partner_cumul_balance
                # Account has move lines with no partner defined
                # if account_data[account]['move_lines']:
                #     previous_cumul_balance =
                #     for key, move_line in account_data[account]['move_lines'].items():
        # Prepare Cumul. Balance
        print(account_data)
        from sys import getsizeof
        print(getsizeof(account_data))

