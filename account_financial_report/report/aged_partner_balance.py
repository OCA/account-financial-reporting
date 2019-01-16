# © 2016 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class AgedPartnerBalanceReport(models.TransientModel):
    """ Here, we just define class fields.
    For methods, go more bottom at this file.

    The class hierarchy is :
    * AgedPartnerBalanceReport
    ** AgedPartnerBalanceReportAccount
    *** AgedPartnerBalanceReportPartner
    **** AgedPartnerBalanceReportLine
    **** AgedPartnerBalanceReportMoveLine
            If "show_move_line_details" is selected
    """

    _name = 'report_aged_partner_balance'
    _inherit = 'account_financial_report_abstract'

    # Filters fields, used for data computation
    date_at = fields.Date()
    only_posted_moves = fields.Boolean()
    company_id = fields.Many2one(comodel_name='res.company')
    filter_account_ids = fields.Many2many(comodel_name='account.account')
    filter_partner_ids = fields.Many2many(comodel_name='res.partner')
    show_move_line_details = fields.Boolean()

    # Open Items Report Data fields, used as base for compute the data reports
    open_items_id = fields.Many2one(comodel_name='report_open_items')

    # Data fields, used to browse report data
    account_ids = fields.One2many(
        comodel_name='report_aged_partner_balance_account',
        inverse_name='report_id'
    )


class AgedPartnerBalanceReportAccount(models.TransientModel):
    _name = 'report_aged_partner_balance_account'
    _inherit = 'account_financial_report_abstract'
    _order = 'code ASC'

    report_id = fields.Many2one(
        comodel_name='report_aged_partner_balance',
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

    cumul_amount_residual = fields.Float(digits=(16, 2))
    cumul_current = fields.Float(digits=(16, 2))
    cumul_age_30_days = fields.Float(digits=(16, 2))
    cumul_age_60_days = fields.Float(digits=(16, 2))
    cumul_age_90_days = fields.Float(digits=(16, 2))
    cumul_age_120_days = fields.Float(digits=(16, 2))
    cumul_older = fields.Float(digits=(16, 2))

    percent_current = fields.Float(digits=(16, 2))
    percent_age_30_days = fields.Float(digits=(16, 2))
    percent_age_60_days = fields.Float(digits=(16, 2))
    percent_age_90_days = fields.Float(digits=(16, 2))
    percent_age_120_days = fields.Float(digits=(16, 2))
    percent_older = fields.Float(digits=(16, 2))

    # Data fields, used to browse report data
    partner_ids = fields.One2many(
        comodel_name='report_aged_partner_balance_partner',
        inverse_name='report_account_id'
    )


class AgedPartnerBalanceReportPartner(models.TransientModel):
    _name = 'report_aged_partner_balance_partner'
    _inherit = 'account_financial_report_abstract'

    report_account_id = fields.Many2one(
        comodel_name='report_aged_partner_balance_account',
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

    # Data fields, used to browse report data
    move_line_ids = fields.One2many(
        comodel_name='report_aged_partner_balance_move_line',
        inverse_name='report_partner_id'
    )
    line_ids = fields.One2many(
        comodel_name='report_aged_partner_balance_line',
        inverse_name='report_partner_id'
    )

    @api.model
    def _generate_order_by(self, order_spec, query):
        """Custom order to display "No partner allocated" at last position."""
        return """
ORDER BY
    CASE
        WHEN
            "report_aged_partner_balance_partner"."partner_id" IS NOT NULL
        THEN 0
        ELSE 1
    END,
    "report_aged_partner_balance_partner"."name"
        """


class AgedPartnerBalanceReportLine(models.TransientModel):
    _name = 'report_aged_partner_balance_line'
    _inherit = 'account_financial_report_abstract'

    report_partner_id = fields.Many2one(
        comodel_name='report_aged_partner_balance_partner',
        ondelete='cascade',
        index=True
    )

    # Data fields, used for report display
    partner = fields.Char()
    amount_residual = fields.Float(digits=(16, 2))
    current = fields.Float(digits=(16, 2))
    age_30_days = fields.Float(digits=(16, 2))
    age_60_days = fields.Float(digits=(16, 2))
    age_90_days = fields.Float(digits=(16, 2))
    age_120_days = fields.Float(digits=(16, 2))
    older = fields.Float(digits=(16, 2))


class AgedPartnerBalanceReportMoveLine(models.TransientModel):
    _name = 'report_aged_partner_balance_move_line'
    _inherit = 'account_financial_report_abstract'

    report_partner_id = fields.Many2one(
        comodel_name='report_aged_partner_balance_partner',
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

    amount_residual = fields.Float(digits=(16, 2))
    current = fields.Float(digits=(16, 2))
    age_30_days = fields.Float(digits=(16, 2))
    age_60_days = fields.Float(digits=(16, 2))
    age_90_days = fields.Float(digits=(16, 2))
    age_120_days = fields.Float(digits=(16, 2))
    older = fields.Float(digits=(16, 2))


class AgedPartnerBalanceReportCompute(models.TransientModel):
    """ Here, we just define methods.
    For class fields, go more top at this file.
    """

    _inherit = 'report_aged_partner_balance'

    @api.multi
    def print_report(self, report_type):
        self.ensure_one()
        if report_type == 'xlsx':
            report_name = 'a_f_r.report_aged_partner_balance_xlsx'
        else:
            report_name = 'account_financial_report.' \
                          'report_aged_partner_balance_qweb'
        report = self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('report_type', '=', report_type)], limit=1)
        return report.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'account_financial_report.report_aged_partner_balance').render(
                    rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self._get_html()

    def _prepare_report_open_items(self):
        self.ensure_one()
        return {
            'date_at': self.date_at,
            'only_posted_moves': self.only_posted_moves,
            'company_id': self.company_id.id,
            'filter_account_ids': [(6, 0, self.filter_account_ids.ids)],
            'filter_partner_ids': [(6, 0, self.filter_partner_ids.ids)],
        }

    @api.multi
    def compute_data_for_report(self):
        self.ensure_one()
        # Compute Open Items Report Data.
        # The data of Aged Partner Balance Report
        # are based on Open Items Report data.
        model = self.env['report_open_items']
        self.open_items_id = model.create(self._prepare_report_open_items())
        self.open_items_id.compute_data_for_report()

        # Compute report data
        self._inject_account_values()
        self._inject_partner_values()
        self._inject_line_values()
        self._inject_line_values(only_empty_partner_line=True)
        if self.show_move_line_details:
            self._inject_move_line_values()
            self._inject_move_line_values(only_empty_partner_line=True)
        self._compute_accounts_cumul()
        # Refresh cache because all data are computed with SQL requests
        self.invalidate_cache()

    def _inject_account_values(self):
        """Inject report values for report_aged_partner_balance_account"""
        query_inject_account = """
INSERT INTO
    report_aged_partner_balance_account
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
    rao.account_id,
    rao.code,
    rao.name
FROM
    report_open_items_account rao
WHERE
    rao.report_id = %s
        """
        query_inject_account_params = (
            self.id,
            self.env.uid,
            self.open_items_id.id,
        )
        self.env.cr.execute(query_inject_account, query_inject_account_params)

    def _inject_partner_values(self):
        """Inject report values for report_aged_partner_balance_partner"""
        query_inject_partner = """
INSERT INTO
    report_aged_partner_balance_partner
    (
    report_account_id,
    create_uid,
    create_date,
    partner_id,
    name
    )
SELECT
    ra.id AS report_account_id,
    %s AS create_uid,
    NOW() AS create_date,
    rpo.partner_id,
    rpo.name
FROM
    report_open_items_partner rpo
INNER JOIN
    report_open_items_account rao ON rpo.report_account_id = rao.id
INNER JOIN
    report_aged_partner_balance_account ra ON rao.code = ra.code
WHERE
    rao.report_id = %s
AND ra.report_id = %s
        """
        query_inject_partner_params = (
            self.env.uid,
            self.open_items_id.id,
            self.id,
        )
        self.env.cr.execute(query_inject_partner, query_inject_partner_params)

    def _inject_line_values(self, only_empty_partner_line=False):
        """ Inject report values for report_aged_partner_balance_line.

        The "only_empty_partner_line" value is used
        to compute data without partner.
        """
        query_inject_line = """
WITH
    date_range AS
        (
            SELECT
                DATE %s AS date_current,
                DATE %s - INTEGER '30' AS date_less_30_days,
                DATE %s - INTEGER '60' AS date_less_60_days,
                DATE %s - INTEGER '90' AS date_less_90_days,
                DATE %s - INTEGER '120' AS date_less_120_days
        )
INSERT INTO
    report_aged_partner_balance_line
    (
        report_partner_id,
        create_uid,
        create_date,
        partner,
        amount_residual,
        current,
        age_30_days,
        age_60_days,
        age_90_days,
        age_120_days,
        older
    )
SELECT
    rp.id AS report_partner_id,
    %s AS create_uid,
    NOW() AS create_date,
    rp.name,
    SUM(rlo.amount_residual) AS amount_residual,
    SUM(
        CASE
            WHEN rlo.date_due >= date_range.date_current
            THEN rlo.amount_residual
        END
    ) AS current,
    SUM(
        CASE
            WHEN
                rlo.date_due >= date_range.date_less_30_days
                AND rlo.date_due < date_range.date_current
            THEN rlo.amount_residual
        END
    ) AS age_30_days,
    SUM(
        CASE
            WHEN
                rlo.date_due >= date_range.date_less_60_days
                AND rlo.date_due < date_range.date_less_30_days
            THEN rlo.amount_residual
        END
    ) AS age_60_days,
    SUM(
        CASE
            WHEN
                rlo.date_due >= date_range.date_less_90_days
                AND rlo.date_due < date_range.date_less_60_days
            THEN rlo.amount_residual
        END
    ) AS age_90_days,
    SUM(
        CASE
            WHEN
                rlo.date_due >= date_range.date_less_120_days
                AND rlo.date_due < date_range.date_less_90_days
            THEN rlo.amount_residual
        END
    ) AS age_120_days,
    SUM(
        CASE
            WHEN rlo.date_due < date_range.date_less_120_days
            THEN rlo.amount_residual
        END
    ) AS older
FROM
    date_range,
    report_open_items_move_line rlo
INNER JOIN
    report_open_items_partner rpo ON rlo.report_partner_id = rpo.id
INNER JOIN
    report_open_items_account rao ON rpo.report_account_id = rao.id
INNER JOIN
    report_aged_partner_balance_account ra ON rao.code = ra.code
INNER JOIN
    report_aged_partner_balance_partner rp
        ON
            ra.id = rp.report_account_id
        """
        if not only_empty_partner_line:
            query_inject_line += """
        AND rpo.partner_id = rp.partner_id
            """
        elif only_empty_partner_line:
            query_inject_line += """
        AND rpo.partner_id IS NULL
        AND rp.partner_id IS NULL
            """
        query_inject_line += """
WHERE
    rao.report_id = %s
AND ra.report_id = %s
GROUP BY
    rp.id
        """
        query_inject_line_params = (self.date_at,) * 5
        query_inject_line_params += (
            self.env.uid,
            self.open_items_id.id,
            self.id,
        )
        self.env.cr.execute(query_inject_line, query_inject_line_params)

    def _inject_move_line_values(self, only_empty_partner_line=False):
        """ Inject report values for report_aged_partner_balance_move_line

        The "only_empty_partner_line" value is used
        to compute data without partner.
        """
        query_inject_move_line = """
WITH
    date_range AS
        (
            SELECT
                DATE %s AS date_current,
                DATE %s - INTEGER '30' AS date_less_30_days,
                DATE %s - INTEGER '60' AS date_less_60_days,
                DATE %s - INTEGER '90' AS date_less_90_days,
                DATE %s - INTEGER '120' AS date_less_120_days
        )
INSERT INTO
    report_aged_partner_balance_move_line
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
        amount_residual,
        current,
        age_30_days,
        age_60_days,
        age_90_days,
        age_120_days,
        older
    )
SELECT
    rp.id AS report_partner_id,
    %s AS create_uid,
    NOW() AS create_date,
    rlo.move_line_id,
    rlo.date,
    rlo.date_due,
    rlo.entry,
    rlo.journal,
    rlo.account,
    rlo.partner,
    rlo.label,
    rlo.amount_residual AS amount_residual,
    CASE
        WHEN rlo.date_due >= date_range.date_current
        THEN rlo.amount_residual
    END AS current,
    CASE
        WHEN
            rlo.date_due >= date_range.date_less_30_days
            AND rlo.date_due < date_range.date_current
        THEN rlo.amount_residual
    END AS age_30_days,
    CASE
        WHEN
            rlo.date_due >= date_range.date_less_60_days
            AND rlo.date_due < date_range.date_less_30_days
        THEN rlo.amount_residual
    END AS age_60_days,
    CASE
        WHEN
            rlo.date_due >= date_range.date_less_90_days
            AND rlo.date_due < date_range.date_less_60_days
        THEN rlo.amount_residual
    END AS age_90_days,
    CASE
        WHEN
            rlo.date_due >= date_range.date_less_120_days
            AND rlo.date_due < date_range.date_less_90_days
        THEN rlo.amount_residual
    END AS age_120_days,
    CASE
        WHEN rlo.date_due < date_range.date_less_120_days
        THEN rlo.amount_residual
    END AS older
FROM
    date_range,
    report_open_items_move_line rlo
INNER JOIN
    report_open_items_partner rpo ON rlo.report_partner_id = rpo.id
INNER JOIN
    report_open_items_account rao ON rpo.report_account_id = rao.id
INNER JOIN
    report_aged_partner_balance_account ra ON rao.code = ra.code
INNER JOIN
    report_aged_partner_balance_partner rp
        ON
            ra.id = rp.report_account_id
        """
        if not only_empty_partner_line:
            query_inject_move_line += """
        AND rpo.partner_id = rp.partner_id
            """
        elif only_empty_partner_line:
            query_inject_move_line += """
        AND rpo.partner_id IS NULL
        AND rp.partner_id IS NULL
            """
        query_inject_move_line += """
WHERE
    rao.report_id = %s
AND ra.report_id = %s
        """
        query_inject_move_line_params = (self.date_at,) * 5
        query_inject_move_line_params += (
            self.env.uid,
            self.open_items_id.id,
            self.id,
        )
        self.env.cr.execute(query_inject_move_line,
                            query_inject_move_line_params)

    def _compute_accounts_cumul(self):
        """ Compute cumulative amount for
        report_aged_partner_balance_account.
        """
        query_compute_accounts_cumul = """
WITH
    cumuls AS
        (
            SELECT
                ra.id AS report_account_id,
                SUM(rl.amount_residual) AS cumul_amount_residual,
                SUM(rl.current) AS cumul_current,
                SUM(rl.age_30_days) AS cumul_age_30_days,
                SUM(rl.age_60_days) AS cumul_age_60_days,
                SUM(rl.age_90_days) AS cumul_age_90_days,
                SUM(rl.age_120_days) AS cumul_age_120_days,
                SUM(rl.older) AS cumul_older
            FROM
                report_aged_partner_balance_line rl
            INNER JOIN
                report_aged_partner_balance_partner rp
                    ON rl.report_partner_id = rp.id
            INNER JOIN
                report_aged_partner_balance_account ra
                    ON rp.report_account_id = ra.id
            WHERE
                ra.report_id = %s
            GROUP BY
                ra.id
        )
UPDATE
    report_aged_partner_balance_account
SET
    cumul_amount_residual = c.cumul_amount_residual,
    cumul_current = c.cumul_current,
    cumul_age_30_days = c.cumul_age_30_days,
    cumul_age_60_days = c.cumul_age_60_days,
    cumul_age_90_days = c.cumul_age_90_days,
    cumul_age_120_days = c.cumul_age_120_days,
    cumul_older = c.cumul_older,
    percent_current =
        CASE
            WHEN c.cumul_amount_residual != 0
            THEN 100 * c.cumul_current / c.cumul_amount_residual
        END,
    percent_age_30_days =
        CASE
            WHEN c.cumul_amount_residual != 0
            THEN 100 * c.cumul_age_30_days / c.cumul_amount_residual
        END,
    percent_age_60_days =
        CASE
            WHEN c.cumul_amount_residual != 0
            THEN 100 * c.cumul_age_60_days / c.cumul_amount_residual
        END,
    percent_age_90_days =
        CASE
            WHEN c.cumul_amount_residual != 0
            THEN 100 * c.cumul_age_90_days / c.cumul_amount_residual
        END,
    percent_age_120_days =
        CASE
            WHEN c.cumul_amount_residual != 0
            THEN 100 * c.cumul_age_120_days / c.cumul_amount_residual
        END,
    percent_older =
        CASE
            WHEN c.cumul_amount_residual != 0
            THEN 100 * c.cumul_older / c.cumul_amount_residual
        END
FROM
    cumuls c
WHERE
    id = c.report_account_id
        """
        params_compute_accounts_cumul = (self.id,)
        self.env.cr.execute(query_compute_accounts_cumul,
                            params_compute_accounts_cumul)
