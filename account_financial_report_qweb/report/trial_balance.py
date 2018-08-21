# -*- coding: utf-8 -*-
# © 2016 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class TrialBalanceReport(models.TransientModel):
    """ Here, we just define class fields.
    For methods, go more bottom at this file.

    The class hierarchy is :
    * TrialBalanceReport
    ** TrialBalanceReportAccount
    *** TrialBalanceReportPartner
            If "show_partner_details" is selected
    """

    _name = 'report_trial_balance_qweb'
    _inherit = 'report_qweb_abstract'

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()
    fy_start_date = fields.Date()
    only_posted_moves = fields.Boolean()
    hide_account_balance_at_0 = fields.Boolean()
    foreign_currency = fields.Boolean()
    company_id = fields.Many2one(comodel_name='res.company')
    filter_account_ids = fields.Many2many(comodel_name='account.account')
    filter_partner_ids = fields.Many2many(comodel_name='res.partner')
    filter_journal_ids = fields.Many2many(comodel_name='account.journal')
    show_partner_details = fields.Boolean()

    # General Ledger Report Data fields,
    # used as base for compute the data reports
    general_ledger_id = fields.Many2one(
        comodel_name='report_general_ledger_qweb'
    )

    # Data fields, used to browse report data
    account_ids = fields.One2many(
        comodel_name='report_trial_balance_qweb_account',
        inverse_name='report_id'
    )


class TrialBalanceReportAccount(models.TransientModel):

    _name = 'report_trial_balance_qweb_account'
    _inherit = 'report_qweb_abstract'
    _order = 'code ASC'

    report_id = fields.Many2one(
        comodel_name='report_trial_balance_qweb',
        ondelete='cascade',
        index=True
    )

    # Data fields, used to keep link with real object
    sequence = fields.Integer(index=True, default=0)
    level = fields.Integer(index=True, default=0)

    # Data fields, used to keep link with real object
    account_id = fields.Many2one(
        'account.account',
        index=True
    )

    # Data fields, used for report display
    code = fields.Char()
    name = fields.Char()

    initial_balance = fields.Float(digits=(16, 2))
    initial_balance_foreign_currency = fields.Float(digits=(16, 2))
    debit = fields.Float(digits=(16, 2))
    credit = fields.Float(digits=(16, 2))
    currency_id = fields.Many2one(comodel_name='res.currency')
    final_balance = fields.Float(digits=(16, 2))
    final_balance_foreign_currency = fields.Float(digits=(16, 2))

    # Data fields, used to browse report data
    partner_ids = fields.One2many(
        comodel_name='report_trial_balance_qweb_partner',
        inverse_name='report_account_id'
    )


class TrialBalanceReportPartner(models.TransientModel):

    _name = 'report_trial_balance_qweb_partner'
    _inherit = 'report_qweb_abstract'

    report_account_id = fields.Many2one(
        comodel_name='report_trial_balance_qweb_account',
        ondelete='cascade',
        index=True
    )

    # Data fields, used to keep link with real object
    partner_id = fields.Many2one(
        'res.partner',
        index=True
    )

    # Data fields, used for report display
    name = fields.Char()

    initial_balance = fields.Float(digits=(16, 2))
    initial_balance_foreign_currency = fields.Float(digits=(16, 2))
    debit = fields.Float(digits=(16, 2))
    credit = fields.Float(digits=(16, 2))
    currency_id = fields.Many2one(comodel_name='res.currency')
    final_balance = fields.Float(digits=(16, 2))
    final_balance_foreign_currency = fields.Float(digits=(16, 2))

    @api.model
    def _generate_order_by(self, order_spec, query):
        """Custom order to display "No partner allocated" at last position."""
        return """
ORDER BY
    CASE
        WHEN "report_trial_balance_qweb_partner"."partner_id" IS NOT NULL
        THEN 0
        ELSE 1
    END,
    "report_trial_balance_qweb_partner"."name"
        """


class TrialBalanceReportCompute(models.TransientModel):
    """ Here, we just define methods.
    For class fields, go more top at this file.
    """

    _inherit = 'report_trial_balance_qweb'

    @api.multi
    def print_report(self, report_type):
        self.ensure_one()
        if report_type == 'xlsx':
            report_name = 'account_financial_report_qweb.' \
                          'report_trial_balance_xlsx'
        else:
            report_name = 'account_financial_report_qweb.' \
                          'report_trial_balance_qweb'
        return self.env['report'].get_action(docids=self.ids,
                                             report_name=report_name)

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'account_financial_report_qweb.'
                'report_trial_balance_html').render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self._get_html()

    def _prepare_report_general_ledger(self, account_ids):
        self.ensure_one()
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'only_posted_moves': self.only_posted_moves,
            'hide_account_balance_at_0': self.hide_account_balance_at_0,
            'foreign_currency': self.foreign_currency,
            'company_id': self.company_id.id,
            'filter_account_ids': [(6, 0, account_ids.ids)],
            'filter_partner_ids': [(6, 0, self.filter_partner_ids.ids)],
            'filter_journal_ids': [(6, 0, self.filter_journal_ids.ids)],
            'fy_start_date': self.fy_start_date,
        }

    @api.multi
    def compute_data_for_report(self):
        self.ensure_one()
        # Compute General Ledger Report Data.
        # The data of Trial Balance Report
        # are based on General Ledger Report data.
        model = self.env['report_general_ledger_qweb']
        if self.filter_account_ids:
            account_ids = self.filter_account_ids
        else:
            account_ids = self.env['account.account'].search(
                [('company_id', '=', self.company_id.id)])
        self.general_ledger_id = model.create(
            self._prepare_report_general_ledger(account_ids)
        )
        self.general_ledger_id.compute_data_for_report(
            with_line_details=False, with_partners=self.show_partner_details
        )

        # Compute report data
        self._inject_account_values(account_ids)
        if self.show_partner_details:
            self._inject_partner_values()
        # Refresh cache because all data are computed with SQL requests
        self.invalidate_cache()

    def _inject_account_values(self, account_ids):
        """Inject report values for report_trial_balance_qweb_account"""
        query_inject_account = """
INSERT INTO
    report_trial_balance_qweb_account
    (
    report_id,
    create_uid,
    create_date,
    account_id,
    code,
    name,
    initial_balance,
    debit,
    credit,
    final_balance,
    currency_id,
    initial_balance_foreign_currency,
    final_balance_foreign_currency
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    acc.id,
    acc.code,
    acc.name,
    coalesce(rag.initial_balance, 0) AS initial_balance,
    coalesce(rag.final_debit - rag.initial_debit, 0) AS debit,
    coalesce(rag.final_credit - rag.initial_credit, 0) AS credit,
    coalesce(rag.final_balance, 0) AS final_balance,
    rag.currency_id AS currency_id,
    coalesce(rag.initial_balance_foreign_currency, 0)
        AS initial_balance_foreign_currency,
    coalesce(rag.final_balance_foreign_currency, 0)
        AS final_balance_foreign_currency
FROM
    account_account acc
    LEFT OUTER JOIN report_general_ledger_qweb_account AS rag
        ON rag.account_id = acc.id AND rag.report_id = %s
WHERE
    acc.id in %s
        """
        if self.hide_account_balance_at_0:
            query_inject_account += """ AND
    final_balance IS NOT NULL AND final_balance != 0"""
        query_inject_account_params = (
            self.id,
            self.env.uid,
            self.general_ledger_id.id,
            account_ids._ids,
        )
        self.env.cr.execute(query_inject_account, query_inject_account_params)

    def _inject_partner_values(self):
        """Inject report values for report_trial_balance_qweb_partner"""
        query_inject_partner = """
INSERT INTO
    report_trial_balance_qweb_partner
    (
    report_account_id,
    create_uid,
    create_date,
    partner_id,
    name,
    initial_balance,
    initial_balance_foreign_currency,
    debit,
    credit,
    final_balance,
    final_balance_foreign_currency
    )
SELECT
    ra.id AS report_account_id,
    %s AS create_uid,
    NOW() AS create_date,
    rpg.partner_id,
    rpg.name,
    rpg.initial_balance AS initial_balance,
    rpg.initial_balance_foreign_currency AS initial_balance_foreign_currency,
    rpg.final_debit - rpg.initial_debit AS debit,
    rpg.final_credit - rpg.initial_credit AS credit,
    rpg.final_balance AS final_balance,
    rpg.final_balance_foreign_currency AS final_balance_foreign_currency
FROM
    report_general_ledger_qweb_partner rpg
INNER JOIN
    report_general_ledger_qweb_account rag ON rpg.report_account_id = rag.id
INNER JOIN
    report_trial_balance_qweb_account ra ON rag.code = ra.code
WHERE
    rag.report_id = %s
AND ra.report_id = %s
        """
        query_inject_partner_params = (
            self.env.uid,
            self.general_ledger_id.id,
            self.id,
        )
        self.env.cr.execute(query_inject_partner, query_inject_partner_params)
