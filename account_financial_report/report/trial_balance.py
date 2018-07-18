# © 2016 Julien Coux (Camptocamp)
# © 2018 Forest and Biomass Romania SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class TrialBalanceReport(models.TransientModel):
    """ Here, we just define class fields.
    For methods, go more bottom at this file.

    The class hierarchy is :
    * TrialBalanceReport
    *** TrialBalanceReportAccount
    **** TrialBalanceReportPartner
            If "show_partner_details" is selected
    """

    _name = 'report_trial_balance'

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
    show_partner_details = fields.Boolean()
    hierarchy_on = fields.Selection([('computed', 'Computed Accounts'),
                                     ('relation', 'Child Accounts')],
                                    string='Hierarchy On',
                                    required=True,
                                    default='computed')

    # General Ledger Report Data fields,
    # used as base for compute the data reports
    general_ledger_id = fields.Many2one(
        comodel_name='report_general_ledger'
    )

    # Data fields, used to browse report data
    account_ids = fields.One2many(
        comodel_name='report_trial_balance_account',
        inverse_name='report_id'
    )


class TrialBalanceReportAccount(models.TransientModel):
    _name = 'report_trial_balance_account'
    _order = 'sequence, code ASC, name'

    report_id = fields.Many2one(
        comodel_name='report_trial_balance',
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

    account_group_id = fields.Many2one(
        'account.group',
        index=True
    )
    parent_id = fields.Many2one(
        'account.group',
        index=True
    )
    child_account_ids = fields.Char(
        string="Accounts")
    compute_account_ids = fields.Many2many(
        'account.account',
        string="Accounts", store=True)

    # Data fields, used for report display
    code = fields.Char()
    name = fields.Char()

    currency_id = fields.Many2one('res.currency')
    initial_balance = fields.Float(digits=(16, 2))
    initial_balance_foreign_currency = fields.Float(digits=(16, 2))
    debit = fields.Float(digits=(16, 2))
    credit = fields.Float(digits=(16, 2))
    final_balance = fields.Float(digits=(16, 2))
    final_balance_foreign_currency = fields.Float(digits=(16, 2))

    # Data fields, used to browse report data
    partner_ids = fields.One2many(
        comodel_name='report_trial_balance_partner',
        inverse_name='report_account_id'
    )


class TrialBalanceReportPartner(models.TransientModel):
    _name = 'report_trial_balance_partner'

    report_account_id = fields.Many2one(
        comodel_name='report_trial_balance_account',
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

    currency_id = fields.Many2one('res.currency')
    initial_balance = fields.Float(digits=(16, 2))
    initial_balance_foreign_currency = fields.Float(digits=(16, 2))
    debit = fields.Float(digits=(16, 2))
    credit = fields.Float(digits=(16, 2))
    final_balance = fields.Float(digits=(16, 2))
    final_balance_foreign_currency = fields.Float(digits=(16, 2))

    @api.model
    def _generate_order_by(self, order_spec, query):
        """Custom order to display "No partner allocated" at last position."""
        return """
ORDER BY
    CASE
        WHEN "report_trial_balance_partner"."partner_id" IS NOT NULL
        THEN 0
        ELSE 1
    END,
    "report_trial_balance_partner"."name"
        """


class TrialBalanceReportCompute(models.TransientModel):
    """ Here, we just define methods.
    For class fields, go more top at this file.
    """

    _inherit = 'report_trial_balance'

    @api.multi
    def print_report(self, report_type):
        self.ensure_one()
        if report_type == 'xlsx':
            report_name = 'a_f_r.report_trial_balance_xlsx'
        else:
            report_name = 'account_financial_report.' \
                          'report_trial_balance_qweb'
        return self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('report_type', '=', report_type)], limit=1).report_action(self)

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'account_financial_report.report_trial_balance').render(
                    rcontext)
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
            'fy_start_date': self.fy_start_date,
        }

    @api.multi
    def compute_data_for_report(self):
        self.ensure_one()
        # Compute General Ledger Report Data.
        # The data of Trial Balance Report
        # are based on General Ledger Report data.
        model = self.env['report_general_ledger']
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
        if not self.filter_account_ids:
            self._inject_account_group_values()
            if self.hierarchy_on == 'computed':
                self._update_account_group_computed_values()
            else:
                self._update_account_group_child_values()
            self._update_account_sequence()
            self._add_account_group_account_values()
        self.refresh()
        if not self.filter_account_ids:
            self._compute_group_accounts()
        else:
            for line in self.account_ids:
                line.write({'level': 0})

    def _inject_account_values(self, account_ids):
        """Inject report values for report_trial_balance_account"""
        query_inject_account = """
INSERT INTO
    report_trial_balance_account
    (
    report_id,
    create_uid,
    create_date,
    account_id,
    parent_id,
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
    acc.group_id,
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
    LEFT OUTER JOIN report_general_ledger_account AS rag
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
        """Inject report values for report_trial_balance_partner"""
        query_inject_partner = """
INSERT INTO
    report_trial_balance_partner
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
    report_general_ledger_partner rpg
INNER JOIN
    report_general_ledger_account rag ON rpg.report_account_id = rag.id
INNER JOIN
    report_trial_balance_account ra ON rag.code = ra.code
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

    def _inject_account_group_values(self):
        """Inject report values for report_trial_balance_account"""
        query_inject_account_group = """
INSERT INTO
    report_trial_balance_account
    (
    report_id,
    create_uid,
    create_date,
    account_group_id,
    parent_id,
    code,
    name,
    sequence,
    level
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    accgroup.id,
    accgroup.parent_id,
    coalesce(accgroup.code_prefix, accgroup.name),
    accgroup.name,
    accgroup.parent_left * 100000,
    accgroup.level
FROM
    account_group accgroup"""
        query_inject_account_params = (
            self.id,
            self.env.uid,
        )
        self.env.cr.execute(query_inject_account_group,
                            query_inject_account_params)

    def _update_account_group_child_values(self):
        """Compute values for report_trial_balance_account group in child."""
        query_update_account_group = """
WITH computed AS (WITH RECURSIVE cte AS (
   SELECT account_group_id, code, account_group_id AS parent_id,
    initial_balance, initial_balance_foreign_currency, debit, credit,
    final_balance, final_balance_foreign_currency
   FROM   report_trial_balance_account
   WHERE report_id = %s
   GROUP BY report_trial_balance_account.id

   UNION  ALL
   SELECT c.account_group_id, c.code, p.account_group_id,
    p.initial_balance, p.initial_balance_foreign_currency, p.debit, p.credit,
    p.final_balance, p.final_balance_foreign_currency
   FROM   cte c
   JOIN   report_trial_balance_account p USING (parent_id)
    WHERE p.report_id = %s
)
SELECT account_group_id, code,
    sum(initial_balance) AS initial_balance,
    sum(initial_balance_foreign_currency) AS initial_balance_foreign_currency,
    sum(debit) AS debit,
    sum(credit) AS credit,
    sum(final_balance) AS final_balance,
    sum(final_balance_foreign_currency) AS final_balance_foreign_currency
FROM   cte
GROUP BY cte.account_group_id, cte.code
ORDER BY account_group_id
)
UPDATE report_trial_balance_account
SET initial_balance = computed.initial_balance,
    initial_balance_foreign_currency =
        computed.initial_balance_foreign_currency,
    debit = computed.debit,
    credit = computed.credit,
    final_balance = computed.final_balance,
    final_balance_foreign_currency =
        computed.final_balance_foreign_currency
FROM computed
WHERE report_trial_balance_account.account_group_id = computed.account_group_id
    AND report_trial_balance_account.report_id = %s
"""
        query_update_account_params = (self.id, self.id, self.id,)
        self.env.cr.execute(query_update_account_group,
                            query_update_account_params)

    def _add_account_group_account_values(self):
        """Compute values for report_trial_balance_account group in child."""
        query_update_account_group = """
DROP AGGREGATE IF EXISTS array_concat_agg(anyarray);
CREATE AGGREGATE array_concat_agg(anyarray) (
  SFUNC = array_cat,
  STYPE = anyarray
);
WITH aggr AS(WITH computed AS (WITH RECURSIVE cte AS (
   SELECT account_group_id, account_group_id AS parent_id,
    ARRAY[account_id]::int[] as child_account_ids
   FROM   report_trial_balance_account
   WHERE report_id = %s
   GROUP BY report_trial_balance_account.id

   UNION  ALL
   SELECT c.account_group_id, p.account_group_id, ARRAY[p.account_id]::int[]
   FROM   cte c
   JOIN   report_trial_balance_account p USING (parent_id)
    WHERE p.report_id = %s
)
SELECT account_group_id,
    array_concat_agg(DISTINCT child_account_ids)::int[] as child_account_ids
FROM   cte
GROUP BY cte.account_group_id, cte.child_account_ids
ORDER BY account_group_id
)
SELECT account_group_id,
    array_concat_agg(DISTINCT child_account_ids)::int[]
        AS child_account_ids from computed
GROUP BY account_group_id)
UPDATE report_trial_balance_account
SET child_account_ids = aggr.child_account_ids
FROM aggr
WHERE report_trial_balance_account.account_group_id = aggr.account_group_id
    AND report_trial_balance_account.report_id = %s
"""
        query_update_account_params = (self.id, self.id, self.id,)
        self.env.cr.execute(query_update_account_group,
                            query_update_account_params)

    def _update_account_group_computed_values(self):
        """Compute values for report_trial_balance_account group in compute."""
        query_update_account_group = """
WITH RECURSIVE accgroup AS
(SELECT
    accgroup.id,
    sum(coalesce(ra.initial_balance, 0)) as initial_balance,
    sum(coalesce(ra.initial_balance_foreign_currency, 0))
        as initial_balance_foreign_currency,
    sum(coalesce(ra.debit, 0)) as debit,
    sum(coalesce(ra.credit, 0)) as credit,
    sum(coalesce(ra.final_balance, 0)) as final_balance,
    sum(coalesce(ra.final_balance_foreign_currency, 0))
        as final_balance_foreign_currency
 FROM
    account_group accgroup
    LEFT OUTER JOIN account_account AS acc
        ON strpos(acc.code, accgroup.code_prefix) = 1
    LEFT OUTER JOIN report_trial_balance_account AS ra
        ON ra.account_id = acc.id
 WHERE ra.report_id = %s
 GROUP BY accgroup.id
)
UPDATE report_trial_balance_account
SET initial_balance = accgroup.initial_balance,
    initial_balance_foreign_currency =
        accgroup.initial_balance_foreign_currency,
    debit = accgroup.debit,
    credit = accgroup.credit,
    final_balance = accgroup.final_balance,
    final_balance_foreign_currency =
        accgroup.final_balance_foreign_currency

FROM accgroup
WHERE report_trial_balance_account.account_group_id = accgroup.id
"""
        query_update_account_params = (self.id,)
        self.env.cr.execute(query_update_account_group,
                            query_update_account_params)

    def _update_account_sequence(self):
        """Compute sequence, level for report_trial_balance_account account."""
        query_update_account_group = """
UPDATE report_trial_balance_account
SET sequence = newline.sequence + 1,
    level = newline.level + 1
FROM report_trial_balance_account as newline
WHERE newline.account_group_id = report_trial_balance_account.parent_id
    AND report_trial_balance_account.report_id = newline.report_id
    AND report_trial_balance_account.account_id is not null
    AND report_trial_balance_account.report_id = %s"""
        query_update_account_params = (self.id,)
        self.env.cr.execute(query_update_account_group,
                            query_update_account_params)

    def _compute_group_accounts(self):
        groups = self.account_ids.filtered(
            lambda a: a.account_group_id is not False)
        for group in groups:
            if self.hierarchy_on == 'compute':
                group.compute_account_ids = \
                    group.account_group_id.compute_account_ids
            else:
                if group.child_account_ids:
                    chacc = group.child_account_ids.replace(
                        '}', '').replace('{', '').split(',')
                    if 'NULL' in chacc:
                        chacc.remove('NULL')
                    if chacc:
                        group.compute_account_ids = [
                            (6, 0, [int(g) for g in chacc])]
