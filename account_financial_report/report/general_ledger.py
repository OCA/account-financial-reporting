
# © 2016 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class GeneralLedgerReport(models.TransientModel):
    """ Here, we just define class fields.
    For methods, go more bottom at this file.

    The class hierarchy is :
    * GeneralLedgerReport
    ** GeneralLedgerReportAccount
    *** GeneralLedgerReportMoveLine
            For non receivable/payable accounts
            For receivable/payable centralized accounts
    *** GeneralLedgerReportPartner
            For receivable/payable and not centralized accounts
    **** GeneralLedgerReportMoveLine
            For receivable/payable and not centralized accounts
    """

    _name = 'report_general_ledger'
    _inherit = 'account_financial_report_abstract'

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
    filter_cost_center_ids = fields.Many2many(
        comodel_name='account.analytic.account'
    )
    filter_journal_ids = fields.Many2many(
        comodel_name='account.journal',
    )
    centralize = fields.Boolean()

    # Flag fields, used for report display
    show_cost_center = fields.Boolean(
        default=lambda self: self.env.user.has_group(
            'analytic.group_analytic_accounting'
        )
    )

    # Data fields, used to browse report data
    account_ids = fields.One2many(
        comodel_name='report_general_ledger_account',
        inverse_name='report_id'
    )

    # Compute of unaffected earnings account
    @api.depends('company_id')
    def _compute_unaffected_earnings_account(self):
        account_type = self.env.ref('account.data_unaffected_earnings')
        self.unaffected_earnings_account = self.env['account.account'].search(
            [
                ('user_type_id', '=', account_type.id),
                ('company_id', '=', self.company_id.id)
            ])

    unaffected_earnings_account = fields.Many2one(
        comodel_name='account.account',
        compute='_compute_unaffected_earnings_account',
        store=True
    )


class GeneralLedgerReportAccount(models.TransientModel):

    _name = 'report_general_ledger_account'
    _inherit = 'account_financial_report_abstract'
    _order = 'code ASC'

    report_id = fields.Many2one(
        comodel_name='report_general_ledger',
        ondelete='cascade',
        index=True
    )

    # Data fields, used to keep link with real object
    account_id = fields.Many2one(
        'account.account',
        index=True
    )

    # Data fields, used for report display
    code = fields.Char()
    name = fields.Char()
    initial_debit = fields.Float(digits=(16, 2))
    initial_credit = fields.Float(digits=(16, 2))
    initial_balance = fields.Float(digits=(16, 2))
    currency_id = fields.Many2one('res.currency')
    initial_balance_foreign_currency = fields.Float(digits=(16, 2))
    final_debit = fields.Float(digits=(16, 2))
    final_credit = fields.Float(digits=(16, 2))
    final_balance = fields.Float(digits=(16, 2))
    final_balance_foreign_currency = fields.Float(digits=(16, 2))

    # Flag fields, used for report display and for data computation
    is_partner_account = fields.Boolean()

    # Data fields, used to browse report data
    move_line_ids = fields.One2many(
        comodel_name='report_general_ledger_move_line',
        inverse_name='report_account_id'
    )
    partner_ids = fields.One2many(
        comodel_name='report_general_ledger_partner',
        inverse_name='report_account_id'
    )


class GeneralLedgerReportPartner(models.TransientModel):

    _name = 'report_general_ledger_partner'
    _inherit = 'account_financial_report_abstract'

    report_account_id = fields.Many2one(
        comodel_name='report_general_ledger_account',
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
    initial_debit = fields.Float(digits=(16, 2))
    initial_credit = fields.Float(digits=(16, 2))
    initial_balance = fields.Float(digits=(16, 2))
    currency_id = fields.Many2one('res.currency')
    initial_balance_foreign_currency = fields.Float(digits=(16, 2))
    final_debit = fields.Float(digits=(16, 2))
    final_credit = fields.Float(digits=(16, 2))
    final_balance = fields.Float(digits=(16, 2))
    final_balance_foreign_currency = fields.Float(digits=(16, 2))

    # Data fields, used to browse report data
    move_line_ids = fields.One2many(
        comodel_name='report_general_ledger_move_line',
        inverse_name='report_partner_id'
    )

    @api.model
    def _generate_order_by(self, order_spec, query):
        """Custom order to display "No partner allocated" at last position."""
        return """
ORDER BY
    CASE
        WHEN "report_general_ledger_partner"."partner_id" IS NOT NULL
        THEN 0
        ELSE 1
    END,
    "report_general_ledger_partner"."name"
        """


class GeneralLedgerReportMoveLine(models.TransientModel):

    _name = 'report_general_ledger_move_line'
    _inherit = 'account_financial_report_abstract'

    report_account_id = fields.Many2one(
        comodel_name='report_general_ledger_account',
        ondelete='cascade',
        index=True
    )
    report_partner_id = fields.Many2one(
        comodel_name='report_general_ledger_partner',
        ondelete='cascade',
        index=True
    )

    # Data fields, used to keep link with real object
    move_line_id = fields.Many2one('account.move.line')

    # Data fields, used for report display
    date = fields.Date()
    entry = fields.Char()
    journal = fields.Char()
    account = fields.Char()
    taxes_description = fields.Char()
    partner = fields.Char()
    label = fields.Char()
    cost_center = fields.Char()
    matching_number = fields.Char()
    debit = fields.Float(digits=(16, 2))
    credit = fields.Float(digits=(16, 2))
    cumul_balance = fields.Float(digits=(16, 2))
    currency_id = fields.Many2one('res.currency')
    amount_currency = fields.Float(digits=(16, 2))


class GeneralLedgerReportCompute(models.TransientModel):
    """ Here, we just define methods.
    For class fields, go more top at this file.
    """

    _inherit = 'report_general_ledger'

    @api.multi
    def print_report(self, report_type):
        self.ensure_one()
        if report_type == 'xlsx':
            report_name = 'a_f_r.report_general_ledger_xlsx'
        else:
            report_name = 'account_financial_report.' \
                          'report_general_ledger_qweb'
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
                'account_financial_report.report_general_ledger').render(
                    rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self._get_html()

    @api.multi
    def compute_data_for_report(self,
                                with_line_details=True,
                                with_partners=True):
        self.ensure_one()
        # Compute report data
        self._inject_account_values()

        if with_partners:
            self._inject_partner_values()
            if not self.filter_partner_ids:
                self._inject_partner_values(only_empty_partner=True)

        # Add unaffected earnings account
        if (not self.filter_account_ids or
                self.unaffected_earnings_account.id in
                self.filter_account_ids.ids):
            self._inject_unaffected_earnings_account_values()

        # Call this function even if we don't want line details because,
        # we need to compute
        # at least the values for unaffected earnings account
        # In this case, only unaffected earnings account values are computed
        only_unaffected_earnings_account = not with_line_details
        self._inject_line_not_centralized_values(
            only_unaffected_earnings_account=only_unaffected_earnings_account
        )

        if with_line_details:
            self._inject_line_not_centralized_values(
                is_account_line=False,
                is_partner_line=True)

            self._inject_line_not_centralized_values(
                is_account_line=False,
                is_partner_line=True,
                only_empty_partner_line=True)

            if self.centralize:
                self._inject_line_centralized_values()

        # Refresh cache because all data are computed with SQL requests
        self.invalidate_cache()

    def _get_account_sub_subquery_sum_amounts(
            self, include_initial_balance, date_included):
        """ Return subquery used to compute sum amounts on accounts """
        sub_subquery_sum_amounts = """
            SELECT
                a.id AS account_id,
                SUM(ml.debit) AS debit,
                SUM(ml.credit) AS credit,
                SUM(ml.balance) AS balance,
                c.id AS currency_id,
                CASE
                    WHEN c.id IS NOT NULL
                    THEN SUM(ml.amount_currency)
                    ELSE NULL
                END AS balance_currency
            FROM
                accounts a
            INNER JOIN
                account_account_type at ON a.user_type_id = at.id
            INNER JOIN
                account_move_line ml
                    ON a.id = ml.account_id
        """

        if date_included:
            sub_subquery_sum_amounts += """
                AND ml.date <= %s
            """
        else:
            sub_subquery_sum_amounts += """
                AND ml.date < %s
            """

        if not include_initial_balance:
            sub_subquery_sum_amounts += """
                AND at.include_initial_balance != TRUE AND ml.date >= %s
            """
        else:
            sub_subquery_sum_amounts += """
                AND at.include_initial_balance = TRUE
            """

        if self.only_posted_moves:
            sub_subquery_sum_amounts += """
        INNER JOIN
            account_move m ON ml.move_id = m.id AND m.state = 'posted'
            """
        if self.filter_cost_center_ids:
            sub_subquery_sum_amounts += """
        INNER JOIN
            account_analytic_account aa
                ON
                    ml.analytic_account_id = aa.id
                    AND aa.id IN %s
            """
        sub_subquery_sum_amounts += """
        LEFT JOIN
            res_currency c ON a.currency_id = c.id
        """
        sub_subquery_sum_amounts += """
        GROUP BY
            a.id, c.id
        """
        return sub_subquery_sum_amounts

    def _get_final_account_sub_subquery_sum_amounts(self, date_included):
        """ Return final subquery used to compute sum amounts on accounts """
        subquery_sum_amounts = """
            SELECT
                sub.account_id AS account_id,
                SUM(COALESCE(sub.debit, 0.0)) AS debit,
                SUM(COALESCE(sub.credit, 0.0)) AS credit,
                SUM(COALESCE(sub.balance, 0.0)) AS balance,
                MAX(sub.currency_id) AS currency_id,
                SUM(COALESCE(sub.balance_currency, 0.0)) AS balance_currency
            FROM
            (
        """
        subquery_sum_amounts += self._get_account_sub_subquery_sum_amounts(
            include_initial_balance=False, date_included=date_included
        )
        subquery_sum_amounts += """
                UNION
        """
        subquery_sum_amounts += self._get_account_sub_subquery_sum_amounts(
            include_initial_balance=True, date_included=date_included
        )
        subquery_sum_amounts += """
            ) sub
            GROUP BY
                sub.account_id
        """
        return subquery_sum_amounts

    def _inject_account_values(self):
        """Inject report values for report_general_ledger_account."""
        query_inject_account = """
WITH
    accounts AS
        (
            SELECT
                a.id,
                a.code,
                a.name,
                a.internal_type IN ('payable', 'receivable')
                    AS is_partner_account,
                a.user_type_id,
                a.currency_id
            FROM
                account_account a
            """
        if self.filter_partner_ids or self.filter_cost_center_ids:
            query_inject_account += """
            INNER JOIN
                account_move_line ml ON a.id = ml.account_id
            """
        if self.filter_partner_ids:
            query_inject_account += """
            INNER JOIN
                res_partner p ON ml.partner_id = p.id
            """
        if self.filter_cost_center_ids:
            query_inject_account += """
            INNER JOIN
                account_analytic_account aa
                    ON
                        ml.analytic_account_id = aa.id
                        AND aa.id IN %s
            """
        query_inject_account += """
            WHERE
                a.company_id = %s
            AND a.id != %s
                    """
        if self.filter_account_ids:
            query_inject_account += """
            AND
                a.id IN %s
            """
        if self.filter_partner_ids:
            query_inject_account += """
            AND
                p.id IN %s
            """
        if self.filter_partner_ids or self.filter_cost_center_ids:
            query_inject_account += """
            GROUP BY
                a.id
            """

        init_subquery = self._get_final_account_sub_subquery_sum_amounts(
            date_included=False
        )
        final_subquery = self._get_final_account_sub_subquery_sum_amounts(
            date_included=True
        )

        query_inject_account += """
        ),
    initial_sum_amounts AS ( """ + init_subquery + """ ),
    final_sum_amounts AS ( """ + final_subquery + """ )
INSERT INTO
    report_general_ledger_account
    (
    report_id,
    create_uid,
    create_date,
    account_id,
    code,
    name,
    initial_debit,
    initial_credit,
    initial_balance,
    currency_id,
    initial_balance_foreign_currency,
    final_debit,
    final_credit,
    final_balance,
    final_balance_foreign_currency,
    is_partner_account
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    a.id AS account_id,
    a.code,
    a.name,
    COALESCE(i.debit, 0.0) AS initial_debit,
    COALESCE(i.credit, 0.0) AS initial_credit,
    COALESCE(i.balance, 0.0) AS initial_balance,
    c.id AS currency_id,
    COALESCE(i.balance_currency, 0.0) AS initial_balance_foreign_currency,
    COALESCE(f.debit, 0.0) AS final_debit,
    COALESCE(f.credit, 0.0) AS final_credit,
    COALESCE(f.balance, 0.0) AS final_balance,
    COALESCE(f.balance_currency, 0.0) AS final_balance_foreign_currency,
    a.is_partner_account
FROM
    accounts a
LEFT JOIN
    initial_sum_amounts i ON a.id = i.account_id
LEFT JOIN
    final_sum_amounts f ON a.id = f.account_id
LEFT JOIN
    res_currency c ON c.id = a.currency_id
WHERE
    (
        i.debit IS NOT NULL AND i.debit != 0
        OR i.credit IS NOT NULL AND i.credit != 0
        OR i.balance IS NOT NULL AND i.balance != 0
        OR f.debit IS NOT NULL AND f.debit != 0
        OR f.credit IS NOT NULL AND f.credit != 0
        OR f.balance IS NOT NULL AND f.balance != 0
    )
        """
        if self.hide_account_balance_at_0:
            query_inject_account += """
AND
    f.balance IS NOT NULL AND f.balance != 0
            """
        query_inject_account_params = ()
        if self.filter_cost_center_ids:
            query_inject_account_params += (
                tuple(self.filter_cost_center_ids.ids),
            )
        query_inject_account_params += (
            self.company_id.id,
            self.unaffected_earnings_account.id,
        )
        if self.filter_account_ids:
            query_inject_account_params += (
                tuple(self.filter_account_ids.ids),
            )
        if self.filter_partner_ids:
            query_inject_account_params += (
                tuple(self.filter_partner_ids.ids),
            )
        query_inject_account_params += (
            self.date_from,
            self.fy_start_date,
        )
        if self.filter_cost_center_ids:
            query_inject_account_params += (
                tuple(self.filter_cost_center_ids.ids),
            )
        query_inject_account_params += (
            self.date_from,
        )
        if self.filter_cost_center_ids:
            query_inject_account_params += (
                tuple(self.filter_cost_center_ids.ids),
            )
        query_inject_account_params += (
            self.date_to,
            self.fy_start_date,
        )
        if self.filter_cost_center_ids:
            query_inject_account_params += (
                tuple(self.filter_cost_center_ids.ids),
            )
        query_inject_account_params += (
            self.date_to,
        )
        if self.filter_cost_center_ids:
            query_inject_account_params += (
                tuple(self.filter_cost_center_ids.ids),
            )
        query_inject_account_params += (
            self.id,
            self.env.uid,
        )
        self.env.cr.execute(query_inject_account, query_inject_account_params)

    def _get_partner_sub_subquery_sum_amounts(
            self, only_empty_partner, include_initial_balance, date_included
    ):
        """ Return subquery used to compute sum amounts on partners """
        sub_subquery_sum_amounts = """
            SELECT
                ap.account_id AS account_id,
                ap.partner_id AS partner_id,
                SUM(ml.debit) AS debit,
                SUM(ml.credit) AS credit,
                SUM(ml.balance) AS balance,
                c.id as currency_id,
                CASE
                    WHEN c.id IS NOT NULL
                    THEN SUM(ml.amount_currency)
                    ELSE NULL
                END AS balance_currency
            FROM
                accounts_partners ap
            INNER JOIN account_account ac
                ON ac.id = ap.account_id
            LEFT JOIN
                res_currency c ON ac.currency_id = c.id
            INNER JOIN
                account_move_line ml
                    ON ap.account_id = ml.account_id
            """
        if date_included:
            sub_subquery_sum_amounts += """
                    AND ml.date <= %s
            """
        else:
            sub_subquery_sum_amounts += """
                    AND ml.date < %s
            """
        if not only_empty_partner:
            sub_subquery_sum_amounts += """
                    AND ap.partner_id = ml.partner_id
            """
        else:
            sub_subquery_sum_amounts += """
                    AND ap.partner_id IS NULL AND ml.partner_id IS NULL
            """
        if not include_initial_balance:
            sub_subquery_sum_amounts += """
                    AND ap.include_initial_balance != TRUE AND ml.date >= %s
            """
        else:
            sub_subquery_sum_amounts += """
                    AND ap.include_initial_balance = TRUE
            """
        if self.only_posted_moves:
            sub_subquery_sum_amounts += """
            INNER JOIN
                account_move m ON ml.move_id = m.id AND m.state = 'posted'
            """
        if self.filter_cost_center_ids:
            sub_subquery_sum_amounts += """
        INNER JOIN
            account_analytic_account aa
                ON
                    ml.analytic_account_id = aa.id
                    AND aa.id IN %s
            """
        sub_subquery_sum_amounts += """
            GROUP BY
                ap.account_id, ap.partner_id, c.id
        """
        return sub_subquery_sum_amounts

    def _get_final_partner_sub_subquery_sum_amounts(self, only_empty_partner,
                                                    date_included):
        """Return final subquery used to compute sum amounts on partners"""

        subquery_sum_amounts = """

            SELECT
                sub.account_id AS account_id,
                sub.partner_id AS partner_id,
                SUM(COALESCE(sub.debit, 0.0)) AS debit,
                SUM(COALESCE(sub.credit, 0.0)) AS credit,
                SUM(COALESCE(sub.balance, 0.0)) AS balance,
                MAX(sub.currency_id) AS currency_id,
                SUM(COALESCE(sub.balance_currency, 0.0)) AS balance_currency
            FROM
            (
        """
        subquery_sum_amounts += self._get_partner_sub_subquery_sum_amounts(
            only_empty_partner,
            include_initial_balance=False,
            date_included=date_included
        )
        subquery_sum_amounts += """
            UNION
        """
        subquery_sum_amounts += self._get_partner_sub_subquery_sum_amounts(
            only_empty_partner,
            include_initial_balance=True,
            date_included=date_included
        )
        subquery_sum_amounts += """
            ) sub
            GROUP BY
                sub.account_id, sub.partner_id
        """
        return subquery_sum_amounts

    def _inject_partner_values(self, only_empty_partner=False):
        """ Inject report values for report_general_ledger_partner.

        Only for "partner" accounts (payable and receivable).
        """
        # pylint: disable=sql-injection
        query_inject_partner = """
WITH
    accounts_partners AS
        (
            SELECT
                ra.id AS report_account_id,
                a.id AS account_id,
                at.include_initial_balance AS include_initial_balance,
                p.id AS partner_id,
                COALESCE(
                    CASE
                        WHEN
                            NULLIF(p.name, '') IS NOT NULL
                            AND NULLIF(p.ref, '') IS NOT NULL
                        THEN p.name || ' (' || p.ref || ')'
                        ELSE p.name
                    END,
                    '""" + _('No partner allocated') + """'
                ) AS partner_name
            FROM
                report_general_ledger_account ra
            INNER JOIN
                account_account a ON ra.account_id = a.id
            INNER JOIN
                account_account_type at ON a.user_type_id = at.id
            INNER JOIN
                account_move_line ml ON a.id = ml.account_id
            LEFT JOIN
                res_partner p ON ml.partner_id = p.id
                    """
        if self.filter_cost_center_ids:
            query_inject_partner += """
            INNER JOIN
                account_analytic_account aa
                    ON
                        ml.analytic_account_id = aa.id
                        AND aa.id IN %s
            """
        query_inject_partner += """
            WHERE
                ra.report_id = %s
            AND
                ra.is_partner_account = TRUE
        """
        if not only_empty_partner:
            query_inject_partner += """
            AND
                p.id IS NOT NULL
            """
        else:
            query_inject_partner += """
            AND
                p.id IS NULL
            """
        query_inject_partner += """
                        """
        if self.centralize:
            query_inject_partner += """
            AND (a.centralized IS NULL OR a.centralized != TRUE)
            """
        if self.filter_partner_ids:
            query_inject_partner += """
            AND
                p.id IN %s
            """

        init_subquery = self._get_final_partner_sub_subquery_sum_amounts(
            only_empty_partner,
            date_included=False
        )
        final_subquery = self._get_final_partner_sub_subquery_sum_amounts(
            only_empty_partner,
            date_included=True
        )

        query_inject_partner += """
            GROUP BY
                ra.id,
                a.id,
                p.id,
                at.include_initial_balance
        ),
    initial_sum_amounts AS ( """ + init_subquery + """ ),
    final_sum_amounts AS ( """ + final_subquery + """ )
INSERT INTO
    report_general_ledger_partner
    (
    report_account_id,
    create_uid,
    create_date,
    partner_id,
    name,
    initial_debit,
    initial_credit,
    initial_balance,
    currency_id,
    initial_balance_foreign_currency,
    final_debit,
    final_credit,
    final_balance,
    final_balance_foreign_currency
    )
SELECT
    ap.report_account_id,
    %s AS create_uid,
    NOW() AS create_date,
    ap.partner_id,
    ap.partner_name,
    COALESCE(i.debit, 0.0) AS initial_debit,
    COALESCE(i.credit, 0.0) AS initial_credit,
    COALESCE(i.balance, 0.0) AS initial_balance,
    i.currency_id AS currency_id,
    COALESCE(i.balance_currency, 0.0) AS initial_balance_foreign_currency,
    COALESCE(f.debit, 0.0) AS final_debit,
    COALESCE(f.credit, 0.0) AS final_credit,
    COALESCE(f.balance, 0.0) AS final_balance,
    COALESCE(f.balance_currency, 0.0) AS final_balance_foreign_currency
FROM
    accounts_partners ap
LEFT JOIN
    initial_sum_amounts i
        ON
            (
        """
        if not only_empty_partner:
            query_inject_partner += """
                ap.partner_id = i.partner_id
            """
        else:
            query_inject_partner += """
                ap.partner_id IS NULL AND i.partner_id IS NULL
            """
        query_inject_partner += """
            )
            AND ap.account_id = i.account_id
LEFT JOIN
    final_sum_amounts f
        ON
            (
        """
        if not only_empty_partner:
            query_inject_partner += """
                ap.partner_id = f.partner_id
            """
        else:
            query_inject_partner += """
                ap.partner_id IS NULL AND f.partner_id IS NULL
            """
        query_inject_partner += """
            )
            AND ap.account_id = f.account_id
WHERE
    (
        i.debit IS NOT NULL AND i.debit != 0
        OR i.credit IS NOT NULL AND i.credit != 0
        OR i.balance IS NOT NULL AND i.balance != 0
        OR f.debit IS NOT NULL AND f.debit != 0
        OR f.credit IS NOT NULL AND f.credit != 0
        OR f.balance IS NOT NULL AND f.balance != 0
    )
        """
        if self.hide_account_balance_at_0:
            query_inject_partner += """
AND
    f.balance IS NOT NULL AND f.balance != 0
            """
        query_inject_partner_params = ()
        if self.filter_cost_center_ids:
            query_inject_partner_params += (
                tuple(self.filter_cost_center_ids.ids),
            )
        query_inject_partner_params += (
            self.id,
        )
        if self.filter_partner_ids:
            query_inject_partner_params += (
                tuple(self.filter_partner_ids.ids),
            )
        query_inject_partner_params += (
            self.date_from,
            self.fy_start_date,
        )
        if self.filter_cost_center_ids:
            query_inject_partner_params += (
                tuple(self.filter_cost_center_ids.ids),
            )
        query_inject_partner_params += (
            self.date_from,
        )
        if self.filter_cost_center_ids:
            query_inject_partner_params += (
                tuple(self.filter_cost_center_ids.ids),
            )
        query_inject_partner_params += (
            self.date_to,
            self.fy_start_date,
        )
        if self.filter_cost_center_ids:
            query_inject_partner_params += (
                tuple(self.filter_cost_center_ids.ids),
            )
        query_inject_partner_params += (
            self.date_to,
        )
        if self.filter_cost_center_ids:
            query_inject_partner_params += (
                tuple(self.filter_cost_center_ids.ids),
            )
        query_inject_partner_params += (
            self.env.uid,
        )
        self.env.cr.execute(query_inject_partner, query_inject_partner_params)

    def _inject_line_not_centralized_values(
            self,
            is_account_line=True,
            is_partner_line=False,
            only_empty_partner_line=False,
            only_unaffected_earnings_account=False):
        """ Inject report values for report_general_ledger_move_line.

        If centralized option have been chosen,
        only non centralized accounts are computed.

        In function of `is_account_line` and `is_partner_line` values,
        the move_line link is made either with account or either with partner.

        The "only_empty_partner_line" value is used
        to compute data without partner.
        """
        query_inject_move_line = """
INSERT INTO
    report_general_ledger_move_line
    (
        """
        if is_account_line:
            query_inject_move_line += """
    report_account_id,
            """
        elif is_partner_line:
            query_inject_move_line += """
    report_partner_id,
            """
        query_inject_move_line += """
    create_uid,
    create_date,
    move_line_id,
    date,
    entry,
    journal,
    account,
    taxes_description,
    partner,
    label,
    cost_center,
    matching_number,
    debit,
    credit,
    cumul_balance,
    currency_id,
    amount_currency
    )
SELECT
        """
        if is_account_line:
            query_inject_move_line += """
    ra.id AS report_account_id,
            """
        elif is_partner_line:
            query_inject_move_line += """
    rp.id AS report_partner_id,
            """
        query_inject_move_line += """
    %s AS create_uid,
    NOW() AS create_date,
    ml.id AS move_line_id,
    ml.date,
    m.name AS entry,
    j.code AS journal,
    a.code AS account,
    CASE
        WHEN
            ml.tax_line_id is not null
        THEN
            COALESCE(at.description, at.name)
        WHEN
            ml.tax_line_id is null
        THEN
            (SELECT
                array_to_string(
                    array_agg(COALESCE(at.description, at.name)
                ), ', ')
            FROM
                account_move_line_account_tax_rel aml_at_rel
            LEFT JOIN
                account_tax at on (at.id = aml_at_rel.account_tax_id)
            WHERE
                aml_at_rel.account_move_line_id = ml.id)
        ELSE
            ''
    END as taxes_description,
        """
        if not only_empty_partner_line:
            query_inject_move_line += """
    CASE
        WHEN
            NULLIF(p.name, '') IS NOT NULL
            AND NULLIF(p.ref, '') IS NOT NULL
        THEN p.name || ' (' || p.ref || ')'
        ELSE p.name
    END AS partner,
            """
        elif only_empty_partner_line:
            query_inject_move_line += """
    '""" + _('No partner allocated') + """' AS partner,
            """
        query_inject_move_line += """
    CONCAT_WS(' - ', NULLIF(ml.ref, ''), NULLIF(ml.name, '')) AS label,
    aa.name AS cost_center,
    fr.name AS matching_number,
    ml.debit,
    ml.credit,
        """
        if is_account_line:
            query_inject_move_line += """
    ra.initial_balance + (
        SUM(ml.balance)
        OVER (PARTITION BY a.code
              ORDER BY a.code, ml.date, ml.id)
    ) AS cumul_balance,
            """
        elif is_partner_line and not only_empty_partner_line:
            query_inject_move_line += """
    rp.initial_balance + (
        SUM(ml.balance)
        OVER (PARTITION BY a.code, p.name
              ORDER BY a.code, p.name, ml.date, ml.id)
    ) AS cumul_balance,
            """
        elif is_partner_line and only_empty_partner_line:
            query_inject_move_line += """
    rp.initial_balance + (
        SUM(ml.balance)
        OVER (PARTITION BY a.code
              ORDER BY a.code, ml.date, ml.id)
    ) AS cumul_balance,
            """
        query_inject_move_line += """
    c.id AS currency_id,
    ml.amount_currency
FROM
        """
        if is_account_line:
            query_inject_move_line += """
    report_general_ledger_account ra
            """
        elif is_partner_line:
            query_inject_move_line += """
    report_general_ledger_partner rp
INNER JOIN
    report_general_ledger_account ra ON rp.report_account_id = ra.id
            """
        query_inject_move_line += """
INNER JOIN
    account_move_line ml ON ra.account_id = ml.account_id
INNER JOIN
    account_move m ON ml.move_id = m.id
INNER JOIN
    account_journal j ON ml.journal_id = j.id
INNER JOIN
    account_account a ON ml.account_id = a.id
LEFT JOIN
    account_tax at ON ml.tax_line_id = at.id
        """
        if is_account_line:
            query_inject_move_line += """
LEFT JOIN
    res_partner p ON ml.partner_id = p.id
            """
        elif is_partner_line and not only_empty_partner_line:
            query_inject_move_line += """
INNER JOIN
    res_partner p
        ON ml.partner_id = p.id AND rp.partner_id = p.id
            """
        query_inject_move_line += """
LEFT JOIN
    account_full_reconcile fr ON ml.full_reconcile_id = fr.id
LEFT JOIN
    res_currency c ON ml.currency_id = c.id
                    """
        if self.filter_cost_center_ids:
            query_inject_move_line += """
INNER JOIN
    account_analytic_account aa
        ON
            ml.analytic_account_id = aa.id
            AND aa.id IN %s
            """
        else:
            query_inject_move_line += """
LEFT JOIN
    account_analytic_account aa ON ml.analytic_account_id = aa.id
            """
        query_inject_move_line += """
WHERE
    ra.report_id = %s
AND
        """
        if only_unaffected_earnings_account:
            query_inject_move_line += """
    a.id = %s
AND
            """
        if is_account_line:
            query_inject_move_line += """
    (ra.is_partner_account IS NULL OR ra.is_partner_account != TRUE)
            """
        elif is_partner_line:
            query_inject_move_line += """
    ra.is_partner_account = TRUE
            """
        if self.centralize:
            query_inject_move_line += """
AND
    (a.centralized IS NULL OR a.centralized != TRUE)
            """
        query_inject_move_line += """
AND
    ml.date BETWEEN %s AND %s
        """
        if self.only_posted_moves:
            query_inject_move_line += """
AND
    m.state = 'posted'
        """
        if only_empty_partner_line:
            query_inject_move_line += """
AND
    ml.partner_id IS NULL
AND
    rp.partner_id IS NULL
        """
        if self.filter_journal_ids:
            query_inject_move_line += """
AND
    j.id IN %s
            """
        if is_account_line:
            query_inject_move_line += """
ORDER BY
    a.code, ml.date, ml.id
            """
        elif is_partner_line and not only_empty_partner_line:
            query_inject_move_line += """
ORDER BY
    a.code, p.name, ml.date, ml.id
            """
        elif is_partner_line and only_empty_partner_line:
            query_inject_move_line += """
ORDER BY
    a.code, ml.date, ml.id
            """

        query_inject_move_line_params = (
            self.env.uid,
        )
        if self.filter_cost_center_ids:
            query_inject_move_line_params += (
                tuple(self.filter_cost_center_ids.ids),
            )
        query_inject_move_line_params += (
            self.id,
        )
        if only_unaffected_earnings_account:
            query_inject_move_line_params += (
                self.unaffected_earnings_account.id,
            )
        query_inject_move_line_params += (
            self.date_from,
            self.date_to,
        )
        if self.filter_journal_ids:
            query_inject_move_line_params += (tuple(
                self.filter_journal_ids.ids,
            ),)
        self.env.cr.execute(
            query_inject_move_line,
            query_inject_move_line_params
        )

    def _inject_line_centralized_values(self):
        """ Inject report values for report_general_ledger_move_line.

        Only centralized accounts are computed.
        """
        query_inject_move_line_centralized = """
WITH
    move_lines AS
        (
            SELECT
                ml.account_id,
                (
                    DATE_TRUNC('month', ml.date) + interval '1 month'
                                                 - interval '1 day'
                )::date AS date,
                SUM(ml.debit) AS debit,
                SUM(ml.credit) AS credit,
                SUM(ml.balance) AS balance,
                ml.currency_id AS currency_id,
                ml.journal_id as journal_id
            FROM
                report_general_ledger_account ra
            INNER JOIN
                account_move_line ml ON ra.account_id = ml.account_id
            INNER JOIN
                account_move m ON ml.move_id = m.id
            INNER JOIN
                account_account a ON ml.account_id = a.id
        """
        if self.filter_cost_center_ids:
            query_inject_move_line_centralized += """
            INNER JOIN
                account_analytic_account aa
                    ON
                        ml.analytic_account_id = aa.id
                        AND aa.id IN %s
            """
        query_inject_move_line_centralized += """
            WHERE
                ra.report_id = %s
            AND
                a.centralized = TRUE
            AND
                ml.date BETWEEN %s AND %s
        """
        if self.only_posted_moves:
            query_inject_move_line_centralized += """
            AND
                m.state = 'posted'
            """
        query_inject_move_line_centralized += """
            GROUP BY
                ra.id, ml.account_id, a.code, 2, ml.currency_id, ml.journal_id
        )
INSERT INTO
    report_general_ledger_move_line
    (
    report_account_id,
    create_uid,
    create_date,
    date,
    account,
    journal,
    label,
    debit,
    credit,
    cumul_balance
    )
SELECT
    ra.id AS report_account_id,
    %s AS create_uid,
    NOW() AS create_date,
    ml.date,
    a.code AS account,
    j.code AS journal,
    '""" + _('Centralized Entries') + """' AS label,
    ml.debit AS debit,
    ml.credit AS credit,
    ra.initial_balance + (
        SUM(ml.balance)
        OVER (PARTITION BY a.code ORDER BY ml.date)
    ) AS cumul_balance
FROM
    report_general_ledger_account ra
INNER JOIN
    move_lines ml ON ra.account_id = ml.account_id
INNER JOIN
    account_account a ON ml.account_id = a.id
INNER JOIN
    account_journal j ON ml.journal_id = j.id
LEFT JOIN
    res_currency c ON ml.currency_id = c.id
WHERE
    ra.report_id = %s
AND
    (a.centralized IS NOT NULL AND a.centralized = TRUE)
    """
        if self.filter_journal_ids:
            query_inject_move_line_centralized += """
AND
    j.id in %s
            """
        query_inject_move_line_centralized += """
ORDER BY
    a.code, ml.date
        """

        query_inject_move_line_centralized_params = ()
        if self.filter_cost_center_ids:
            query_inject_move_line_centralized_params += (
                tuple(self.filter_cost_center_ids.ids),
            )
        query_inject_move_line_centralized_params += (
            self.id,
            self.date_from,
            self.date_to,
            self.env.uid,
            self.id,
        )
        if self.filter_journal_ids:
            query_inject_move_line_centralized_params += (tuple(
                self.filter_journal_ids.ids,
            ),)
        self.env.cr.execute(
            query_inject_move_line_centralized,
            query_inject_move_line_centralized_params
        )

    def _get_unaffected_earnings_account_sub_subquery_sum_initial(
            self
    ):
        """ Return subquery used to compute sum amounts on
        unaffected earnings accounts """
        sub_subquery_sum_amounts = """
        SELECT
            SUM(ml.balance) AS initial_balance,
            0.0 AS final_balance
        FROM
            account_account a
        INNER JOIN
            account_account_type at ON a.user_type_id = at.id
        INNER JOIN
            account_move_line ml
                ON a.id = ml.account_id
                AND ml.date < %(date_from)s
            """
        if self.only_posted_moves:
            sub_subquery_sum_amounts += """
        INNER JOIN
            account_move m ON ml.move_id = m.id AND m.state = 'posted'
            """
        if self.filter_cost_center_ids:
            sub_subquery_sum_amounts += """
        INNER JOIN
            account_analytic_account aa
                ON
                    ml.analytic_account_id = aa.id
                    AND aa.id IN %(cost_center_ids)s
            """
        sub_subquery_sum_amounts += """
        WHERE
            a.company_id = %(company_id)s
        AND
            a.id IN %(unaffected_earnings_account_ids)s
        """
        if self.filter_journal_ids:
            sub_subquery_sum_amounts += """
        AND
            ml.journal_id in %(filter_journal_ids)s
        """
        return sub_subquery_sum_amounts

    def _get_unaffected_earnings_account_sub_subquery_sum_final(self):
        """ Return subquery used to compute sum amounts on
                unaffected earnings accounts """

        sub_subquery_sum_amounts = """
            SELECT
                0.0 AS initial_balance,
                SUM(ml.balance) AS final_balance
                """
        sub_subquery_sum_amounts += """
                FROM
                    account_account a
                INNER JOIN
                    account_account_type at ON a.user_type_id = at.id
                INNER JOIN
                    account_move_line ml
                        ON a.id = ml.account_id
                        AND ml.date <= %(date_to)s
                """
        if self.only_posted_moves:
            sub_subquery_sum_amounts += """
                INNER JOIN
                    account_move m ON ml.move_id = m.id AND m.state = 'posted'
                    """
        if self.filter_cost_center_ids:
            sub_subquery_sum_amounts += """
                INNER JOIN
                    account_analytic_account aa
                        ON
                            ml.analytic_account_id = aa.id
                            AND aa.id IN %(cost_center_ids)s
                    """
        sub_subquery_sum_amounts += """
        WHERE
            a.company_id = %(company_id)s
        AND
            a.id IN %(unaffected_earnings_account_ids)s
        """
        if self.filter_journal_ids:
            sub_subquery_sum_amounts += """
        AND
            ml.journal_id in %(filter_journal_ids)s
        """
        return sub_subquery_sum_amounts

    def _inject_unaffected_earnings_account_values(self):
        """Inject the report values of the unaffected earnings account
        for report_general_ledger_account."""
        subquery_sum_amounts = """
            SELECT
                SUM(COALESCE(sub.initial_balance, 0.0)) AS initial_balance,
                SUM(COALESCE(sub.final_balance, 0.0)) AS final_balance
            FROM
            (
        """
        # Initial balances
        subquery_sum_amounts += \
            self._get_unaffected_earnings_account_sub_subquery_sum_initial()
        subquery_sum_amounts += """
                UNION
        """
        subquery_sum_amounts += \
            self._get_unaffected_earnings_account_sub_subquery_sum_final()
        subquery_sum_amounts += """
            ) sub
        """

        # pylint: disable=sql-injection
        query_inject_account = """
        WITH
            sum_amounts AS ( """ + subquery_sum_amounts + """ )
        INSERT INTO
            report_general_ledger_account
            (
            report_id,
            create_uid,
            create_date,
            account_id,
            code,
            name,
            is_partner_account,
            initial_balance,
            final_balance,
            currency_id
            )
        SELECT
            %(report_id)s AS report_id,
            %(user_id)s AS create_uid,
            NOW() AS create_date,
            a.id AS account_id,
            a.code,
            a.name,
            False AS is_partner_account,
            COALESCE(i.initial_balance, 0.0) AS initial_balance,
            COALESCE(i.final_balance, 0.0) AS final_balance,
            c.id as currency_id
        FROM
            account_account a
        LEFT JOIN
            res_currency c ON c.id = a.currency_id,
            sum_amounts i
        WHERE
            a.company_id = %(company_id)s
        AND a.id = %(unaffected_earnings_account_id)s
                """
        query_inject_account_params = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'fy_start_date': self.fy_start_date,
        }
        if self.filter_cost_center_ids:
            query_inject_account_params['cost_center_ids'] = \
                tuple(self.filter_cost_center_ids.ids)
        query_inject_account_params['company_id'] = self.company_id.id
        query_inject_account_params['unaffected_earnings_account_id'] = \
            self.unaffected_earnings_account.id
        query_inject_account_params['report_id'] = self.id
        query_inject_account_params['user_id'] = self.env.uid

        if self.filter_journal_ids:
            query_inject_account_params['filter_journal_ids'] = (tuple(
                self.filter_journal_ids.ids,
            ),)
        # Fetch the profit and loss accounts
        query_unaffected_earnings_account_ids = """
            SELECT a.id
            FROM account_account as a
            INNER JOIN account_account_type as at
            ON at.id = a.user_type_id
            WHERE at.include_initial_balance = FALSE
        """
        self.env.cr.execute(query_unaffected_earnings_account_ids)
        pl_account_ids = [r[0] for r in self.env.cr.fetchall()]
        query_inject_account_params['unaffected_earnings_account_ids'] = \
            tuple(pl_account_ids + [self.unaffected_earnings_account.id])
        self.env.cr.execute(query_inject_account,
                            query_inject_account_params)
