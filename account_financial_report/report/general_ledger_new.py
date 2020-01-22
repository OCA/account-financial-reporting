
# © 2016 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

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

    def _get_accounts_domain(self, data, company):
        domain = [('account_id', '!=', self._get_unaffected_earnings_account(company))]
        if data['account_ids']:
            domain += [('account_id', 'in', data['account_ids'])]
        if data['partner_ids']:
            domain += [('partner_id', 'in', data['partner_ids'])]
        if data['analytic_tag_ids']:
            domain += [('analytic_tag_ids', 'in', data['analytic_tag_ids'])]
        return domain

    def _get_accounts(self, wiz, data, company):
        filter_account_ids = self.env['account.move.line'].read_group(
            self._get_accounts_domain(data, company), ['account_id'], ['account_id']
        )
        account_ids = [move_id['account_id'][0] for move_id in filter_account_ids]
        return self.env['account.account'].read_group([('id', 'in', account_ids)], ['code','name','internal_type','user_type_id','currency_id'], ['code'], lazy=False)

    @api.multi
    def _get_report_values(self, docids, data):
        wizard_id = data['wizard_id']
        wizard = self.env['general.ledger.report.wizard'].browse(wizard_id)
        company = self.env['res.company'].browse(data['company_id'])

        account_ids = data['account_ids']
        partner_ids = data['partner_ids']
        analytic_tag_ids = data['analytic_tag_ids']
        account_journal_ids = data['journal_ids']
        cost_center_ids = data['cost_center_ids']

        accounts_data = self._get_accounts(
            wizard, data, company)
        print(accounts_data)
