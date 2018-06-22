# -*- coding: utf-8 -*-
# © 2016 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _


class OpenItemsReport(models.TransientModel):
    """ Here, we just define class fields.
    For methods, go more bottom at this file.

    The class hierarchy is :
    * OpenItemsReport
    ** OpenItemsReportAccount
    *** OpenItemsReportPartner
    **** OpenItemsReportMoveLine
    """

    _name = 'report_open_items_qweb'

    # Filters fields, used for data computation
    date_at = fields.Date()
    only_posted_moves = fields.Boolean()
    hide_account_balance_at_0 = fields.Boolean()
    company_id = fields.Many2one(comodel_name='res.company')
    filter_account_ids = fields.Many2many(comodel_name='account.account')
    filter_partner_ids = fields.Many2many(comodel_name='res.partner')

    # Flag fields, used for report display
    has_second_currency = fields.Boolean()

    # Data fields, used to browse report data
    account_ids = fields.One2many(
        comodel_name='report_open_items_qweb_account',
        inverse_name='report_id'
    )


class OpenItemsReportAccount(models.TransientModel):

    _name = 'report_open_items_qweb_account'
    _order = 'code ASC'

    report_id = fields.Many2one(
        comodel_name='report_open_items_qweb',
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
    final_amount_residual = fields.Float(digits=(16, 2))

    # Data fields, used to browse report data
    partner_ids = fields.One2many(
        comodel_name='report_open_items_qweb_partner',
        inverse_name='report_account_id'
    )


class OpenItemsReportPartner(models.TransientModel):

    _name = 'report_open_items_qweb_partner'

    report_account_id = fields.Many2one(
        comodel_name='report_open_items_qweb_account',
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
    final_amount_residual = fields.Float(digits=(16, 2))

    # Data fields, used to browse report data
    move_line_ids = fields.One2many(
        comodel_name='report_open_items_qweb_move_line',
        inverse_name='report_partner_id'
    )

    @api.model
    def _generate_order_by(self, order_spec, query):
        """Custom order to display "No partner allocated" at last position."""
        return """
ORDER BY
    CASE
        WHEN "report_open_items_qweb_partner"."partner_id" IS NOT NULL
        THEN 0
        ELSE 1
    END,
    "report_open_items_qweb_partner"."name"
        """


class OpenItemsReportMoveLine(models.TransientModel):

    _name = 'report_open_items_qweb_move_line'

    report_partner_id = fields.Many2one(
        comodel_name='report_open_items_qweb_partner',
        ondelete='cascade',
        index=True
    )

    # Data fields, used to keep link with real object
    move_line_id = fields.Many2one('account.move.line')

    # Data fields, used for report display
    date = fields.Date()
    date_due = fields.Date()
    entry = fields.Char()
    journal = fields.Char()
    account = fields.Char()
    partner = fields.Char()
    label = fields.Char()
    amount_total_due = fields.Float(digits=(16, 2))
    amount_residual = fields.Float(digits=(16, 2))
    currency_name = fields.Char()
    amount_total_due_currency = fields.Float(digits=(16, 2))
    amount_residual_currency = fields.Float(digits=(16, 2))


class OpenItemsReportCompute(models.TransientModel):
    """ Here, we just define methods.
    For class fields, go more top at this file.
    """

    _inherit = 'report_open_items_qweb'

    @api.multi
    def print_report(self, xlsx_report=False):
        self.ensure_one()
        self.compute_data_for_report()
        if xlsx_report:
            report_name = 'account_financial_report_qweb.' \
                          'report_open_items_xlsx'
        else:
            report_name = 'account_financial_report_qweb.' \
                          'report_open_items_qweb'
        return self.env['report'].get_action(records=self,
                                             report_name=report_name)

    @api.multi
    def compute_data_for_report(self):
        self.ensure_one()
        # Compute report data
        self._inject_account_values()
        self._inject_partner_values()
        self._inject_line_values()
        self._inject_line_values(only_empty_partner_line=True)
        self._clean_partners_and_accounts()
        self._compute_partners_and_accounts_cumul()
        if self.hide_account_balance_at_0:
            self._clean_partners_and_accounts(
                only_delete_account_balance_at_0=True
            )
        # Compute display flag
        self._compute_has_second_currency()
        # Refresh cache because all data are computed with SQL requests
        self.refresh()

    def _inject_account_values(self):
        """Inject report values for report_open_items_qweb_account."""
        query_inject_account = """
WITH
    accounts AS
        (
            SELECT
                a.id,
                a.code,
                a.name,
                a.user_type_id
            FROM
                account_account a
            INNER JOIN
                account_move_line ml ON a.id = ml.account_id AND ml.date <= %s
            """
        if self.filter_partner_ids:
            query_inject_account += """
            INNER JOIN
                res_partner p ON ml.partner_id = p.id
            """
        if self.only_posted_moves:
            query_inject_account += """
            INNER JOIN
                account_move m ON ml.move_id = m.id AND m.state = 'posted'
            """
        query_inject_account += """
            WHERE
                a.company_id = %s
            AND a.internal_type IN ('payable', 'receivable')
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
        query_inject_account += """
            GROUP BY
                a.id
        )
INSERT INTO
    report_open_items_qweb_account
    (
    report_id,
    create_uid,
    create_date,
    account_id,
    code,
    name
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    a.id AS account_id,
    a.code,
    COALESCE(tr.value, a.name) AS name
FROM
    accounts a
LEFT JOIN
    ir_translation tr ON a.id = tr.res_id
        AND tr.lang = %s
        AND tr.type = 'model'
        AND tr.name = 'account.account,name'
        """
        query_inject_account_params = (
            self.date_at,
            self.company_id.id,
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
            self.id,
            self.env.uid,
            self.env.lang,
        )
        self.env.cr.execute(query_inject_account, query_inject_account_params)

    def _inject_partner_values(self):
        """ Inject report values for report_open_items_qweb_partner. """
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
                report_open_items_qweb_account ra
            INNER JOIN
                account_account a ON ra.account_id = a.id
            INNER JOIN
                account_account_type at ON a.user_type_id = at.id
            INNER JOIN
                account_move_line ml ON a.id = ml.account_id AND ml.date <= %s
        """
        if self.only_posted_moves:
            query_inject_partner += """
            INNER JOIN
                account_move m ON ml.move_id = m.id AND m.state = 'posted'
            """
        query_inject_partner += """
            LEFT JOIN
                res_partner p ON ml.partner_id = p.id
            WHERE
                ra.report_id = %s
                        """
        if self.filter_partner_ids:
            query_inject_partner += """
            AND
                p.id IN %s
            """
        query_inject_partner += """
            GROUP BY
                ra.id,
                a.id,
                p.id,
                at.include_initial_balance
        )
INSERT INTO
    report_open_items_qweb_partner
    (
    report_account_id,
    create_uid,
    create_date,
    partner_id,
    name
    )
SELECT
    ap.report_account_id,
    %s AS create_uid,
    NOW() AS create_date,
    ap.partner_id,
    ap.partner_name
FROM
    accounts_partners ap
        """
        query_inject_partner_params = (
            self.date_at,
            self.id,
        )
        if self.filter_partner_ids:
            query_inject_partner_params += (
                tuple(self.filter_partner_ids.ids),
            )
        query_inject_partner_params += (
            self.env.uid,
        )
        self.env.cr.execute(query_inject_partner, query_inject_partner_params)

    def _get_line_sub_query_move_lines(self,
                                       only_empty_partner_line=False,
                                       positive_balance=True):
        """ Return subquery used to compute sum amounts on lines """
        sub_query = """
            SELECT
                ml.id,
                ml.balance,
                SUM(
                    CASE
                        WHEN ml_past.id IS NOT NULL
                        THEN pr.amount
                        ELSE NULL
                    END
                ) AS partial_amount,
                ml.amount_currency,
                SUM(
                    CASE
                        WHEN ml_past.id IS NOT NULL
                        THEN pr.amount_currency
                        ELSE NULL
                    END
                ) AS partial_amount_currency
            FROM
                report_open_items_qweb_partner rp
            INNER JOIN
                report_open_items_qweb_account ra
                    ON rp.report_account_id = ra.id
            INNER JOIN
                account_move_line ml
                    ON ra.account_id = ml.account_id
        """
        if not only_empty_partner_line:
            sub_query += """
                    AND rp.partner_id = ml.partner_id
            """
        elif only_empty_partner_line:
            sub_query += """
                    AND ml.partner_id IS NULL
            """
        if not positive_balance:
            sub_query += """
            LEFT JOIN
                account_partial_reconcile pr
                    ON ml.balance < 0 AND pr.credit_move_id = ml.id
            LEFT JOIN
                account_move_line ml_future
                    ON ml.balance < 0 AND pr.debit_move_id = ml_future.id
                    AND ml_future.date > %s
            LEFT JOIN
                account_move_line ml_past
                    ON ml.balance < 0 AND pr.debit_move_id = ml_past.id
                    AND ml_past.date <= %s
            """
        else:
            sub_query += """
            LEFT JOIN
                account_partial_reconcile pr
                    ON ml.balance > 0 AND pr.debit_move_id = ml.id
            LEFT JOIN
                account_move_line ml_future
                    ON ml.balance > 0 AND pr.credit_move_id = ml_future.id
                    AND ml_future.date > %s
            LEFT JOIN
                account_move_line ml_past
                    ON ml.balance > 0 AND pr.credit_move_id = ml_past.id
                    AND ml_past.date <= %s
        """
        sub_query += """
            WHERE
                ra.report_id = %s
            GROUP BY
                ml.id,
                ml.balance,
                ml.amount_currency
            HAVING
                (
                    ml.full_reconcile_id IS NULL
                    OR MAX(ml_future.id) IS NOT NULL
                )
        """
        return sub_query

    def _inject_line_values(self, only_empty_partner_line=False):
        """ Inject report values for report_open_items_qweb_move_line.

        The "only_empty_partner_line" value is used
        to compute data without partner.
        """
        query_inject_move_line = """
WITH
    move_lines_amount AS
        (
        """
        query_inject_move_line += self._get_line_sub_query_move_lines(
            only_empty_partner_line=only_empty_partner_line,
            positive_balance=True
        )
        query_inject_move_line += """
            UNION
        """
        query_inject_move_line += self._get_line_sub_query_move_lines(
            only_empty_partner_line=only_empty_partner_line,
            positive_balance=False
        )
        query_inject_move_line += """
        ),
    move_lines AS
        (
            SELECT
                id,
                CASE
                    WHEN SUM(partial_amount) > 0
                    THEN
                        CASE
                            WHEN balance > 0
                            THEN balance - SUM(partial_amount)
                            ELSE balance + SUM(partial_amount)
                        END
                    ELSE balance
                END AS amount_residual,
                CASE
                    WHEN SUM(partial_amount_currency) > 0
                    THEN
                        CASE
                            WHEN amount_currency > 0
                            THEN amount_currency - SUM(partial_amount_currency)
                            ELSE amount_currency + SUM(partial_amount_currency)
                        END
                    ELSE amount_currency
                END AS amount_residual_currency
            FROM
                move_lines_amount
            GROUP BY
                id,
                balance,
                amount_currency
        )
INSERT INTO
    report_open_items_qweb_move_line
    (
    report_partner_id,
    create_uid,
    create_date,
    move_line_id,
    date,
    date_due,
    entry,
    journal,
    account,
    partner,
    label,
    amount_total_due,
    amount_residual,
    currency_name,
    amount_total_due_currency,
    amount_residual_currency
    )
SELECT
    rp.id AS report_partner_id,
    %s AS create_uid,
    NOW() AS create_date,
    ml.id AS move_line_id,
    ml.date,
    ml.date_maturity,
    m.name AS entry,
    j.code AS journal,
    a.code AS account,
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
    ml.balance,
    ml2.amount_residual,
    c.name AS currency_name,
    ml.amount_currency,
    ml2.amount_residual_currency
FROM
    report_open_items_qweb_partner rp
INNER JOIN
    report_open_items_qweb_account ra ON rp.report_account_id = ra.id
INNER JOIN
    account_move_line ml ON ra.account_id = ml.account_id
INNER JOIN
    move_lines ml2
        ON ml.id = ml2.id
        AND ml2.amount_residual IS NOT NULL
        AND ml2.amount_residual != 0
INNER JOIN
    account_move m ON ml.move_id = m.id
INNER JOIN
    account_journal j ON ml.journal_id = j.id
INNER JOIN
    account_account a ON ml.account_id = a.id
        """
        if not only_empty_partner_line:
            query_inject_move_line += """
INNER JOIN
    res_partner p
        ON ml.partner_id = p.id AND rp.partner_id = p.id
            """
        query_inject_move_line += """
LEFT JOIN
    account_full_reconcile fr ON ml.full_reconcile_id = fr.id
LEFT JOIN
    res_currency c ON a.currency_id = c.id
WHERE
    ra.report_id = %s
AND
    ml.date <= %s
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
        if not only_empty_partner_line:
            query_inject_move_line += """
ORDER BY
    a.code, p.name, ml.date, ml.id
            """
        elif only_empty_partner_line:
            query_inject_move_line += """
ORDER BY
    a.code, ml.date, ml.id
            """
        self.env.cr.execute(
            query_inject_move_line,
            (self.date_at,
             self.date_at,
             self.id,
             self.date_at,
             self.date_at,
             self.id,
             self.env.uid,
             self.id,
             self.date_at,)
        )

    def _compute_partners_and_accounts_cumul(self):
        """ Compute cumulative amount for
        report_open_items_qweb_partner and report_open_items_qweb_account.
        """
        query_compute_partners_cumul = """
UPDATE
    report_open_items_qweb_partner
SET
    final_amount_residual =
        (
            SELECT
                SUM(rml.amount_residual) AS final_amount_residual
            FROM
                report_open_items_qweb_move_line rml
            WHERE
                rml.report_partner_id = report_open_items_qweb_partner.id
        )
WHERE
    id IN
        (
            SELECT
                rp.id
            FROM
                report_open_items_qweb_account ra
            INNER JOIN
                report_open_items_qweb_partner rp
                    ON ra.id = rp.report_account_id
            WHERE
                ra.report_id = %s
        )
        """
        params_compute_partners_cumul = (self.id,)
        self.env.cr.execute(query_compute_partners_cumul,
                            params_compute_partners_cumul)
        query_compute_accounts_cumul = """
UPDATE
    report_open_items_qweb_account
SET
    final_amount_residual =
        (
            SELECT
                SUM(rp.final_amount_residual) AS final_amount_residual
            FROM
                report_open_items_qweb_partner rp
            WHERE
                rp.report_account_id = report_open_items_qweb_account.id
        )
WHERE
    report_id  = %s
        """
        params_compute_accounts_cumul = (self.id,)
        self.env.cr.execute(query_compute_accounts_cumul,
                            params_compute_accounts_cumul)

    def _clean_partners_and_accounts(self,
                                     only_delete_account_balance_at_0=False):
        """ Delete empty data for
        report_open_items_qweb_partner and report_open_items_qweb_account.

        The "only_delete_account_balance_at_0" value is used
        to delete also the data with cumulative amounts at 0.
        """
        query_clean_partners = """
DELETE FROM
    report_open_items_qweb_partner
WHERE
    id IN
        (
            SELECT
                DISTINCT rp.id
            FROM
                report_open_items_qweb_account ra
            INNER JOIN
                report_open_items_qweb_partner rp
                    ON ra.id = rp.report_account_id
            LEFT JOIN
                report_open_items_qweb_move_line rml
                    ON rp.id = rml.report_partner_id
            WHERE
                ra.report_id = %s
        """
        if not only_delete_account_balance_at_0:
            query_clean_partners += """
            AND rml.id IS NULL
            """
        elif only_delete_account_balance_at_0:
            query_clean_partners += """
            AND (
                rp.final_amount_residual IS NULL
                OR rp.final_amount_residual = 0
                )
            """
        query_clean_partners += """
        )
        """
        params_clean_partners = (self.id,)
        self.env.cr.execute(query_clean_partners, params_clean_partners)
        query_clean_accounts = """
DELETE FROM
    report_open_items_qweb_account
WHERE
    id IN
        (
            SELECT
                DISTINCT ra.id
            FROM
                report_open_items_qweb_account ra
            LEFT JOIN
                report_open_items_qweb_partner rp
                    ON ra.id = rp.report_account_id
            WHERE
                ra.report_id = %s
        """
        if not only_delete_account_balance_at_0:
            query_clean_accounts += """
            AND rp.id IS NULL
            """
        elif only_delete_account_balance_at_0:
            query_clean_accounts += """
            AND (
                ra.final_amount_residual IS NULL
                OR ra.final_amount_residual = 0
                )
            """
        query_clean_accounts += """
        )
        """
        params_clean_accounts = (self.id,)
        self.env.cr.execute(query_clean_accounts, params_clean_accounts)

    def _compute_has_second_currency(self):
        """ Compute "has_second_currency" flag which will used for display."""
        query_update_has_second_currency = """
UPDATE
    report_open_items_qweb
SET
    has_second_currency =
        (
            SELECT
                TRUE
            FROM
                report_open_items_qweb_move_line l
            INNER JOIN
                report_open_items_qweb_partner p
                    ON l.report_partner_id = p.id
            INNER JOIN
                report_open_items_qweb_account a
                    ON p.report_account_id = a.id
            WHERE
                a.report_id = %s
            AND l.currency_name IS NOT NULL
            LIMIT 1
        )
WHERE id = %s
        """
        params = (self.id,) * 2
        self.env.cr.execute(query_update_has_second_currency, params)
