# -*- coding: utf-8 -*-
# © 2016 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class AgedPartnerBalanceReport(models.TransientModel):
    """ Here, we just define class fields.
    For methods, go more bottom at this file.
    """

    _name = 'report_aged_partner_balance_qweb'

    date_at = fields.Date()
    only_posted_moves = fields.Boolean()
    company_id = fields.Many2one(comodel_name='res.company')
    filter_account_ids = fields.Many2many(comodel_name='account.account')
    filter_partner_ids = fields.Many2many(comodel_name='res.partner')
    show_move_line_details = fields.Boolean()

    open_invoice_id = fields.Many2one(comodel_name='report_open_invoice_qweb')

    account_ids = fields.One2many(
        comodel_name='report_aged_partner_balance_qweb_account',
        inverse_name='report_id'
    )


class AgedPartnerBalanceAccount(models.TransientModel):

    _name = 'report_aged_partner_balance_qweb_account'
    _order = 'code ASC'

    report_id = fields.Many2one(
        comodel_name='report_aged_partner_balance_qweb',
        ondelete='cascade',
        index=True
    )
    account_id = fields.Many2one(
        'account.account',
        index=True
    )
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

    partner_ids = fields.One2many(
        comodel_name='report_aged_partner_balance_qweb_partner',
        inverse_name='report_account_id'
    )


class AgedPartnerBalancePartner(models.TransientModel):

    _name = 'report_aged_partner_balance_qweb_partner'

    report_account_id = fields.Many2one(
        comodel_name='report_aged_partner_balance_qweb_account',
        ondelete='cascade',
        index=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        index=True
    )
    name = fields.Char()

    move_line_ids = fields.One2many(
        comodel_name='report_aged_partner_balance_qweb_move_line',
        inverse_name='report_partner_id'
    )

    line_ids = fields.One2many(
        comodel_name='report_aged_partner_balance_qweb_line',
        inverse_name='report_partner_id'
    )

    @api.model
    def _generate_order_by(self, order_spec, query):
        return """
ORDER BY
CASE
    WHEN "report_aged_partner_balance_qweb_partner"."partner_id" IS NOT NULL
    THEN 0
    ELSE 1
    END,
"report_aged_partner_balance_qweb_partner"."name"
        """


class AgedPartnerBalanceLine(models.TransientModel):

    _name = 'report_aged_partner_balance_qweb_line'

    report_partner_id = fields.Many2one(
        comodel_name='report_aged_partner_balance_qweb_partner',
        ondelete='cascade',
        index=True
    )
    partner = fields.Char()
    amount_residual = fields.Float(digits=(16, 2))
    current = fields.Float(digits=(16, 2))
    age_30_days = fields.Float(digits=(16, 2))
    age_60_days = fields.Float(digits=(16, 2))
    age_90_days = fields.Float(digits=(16, 2))
    age_120_days = fields.Float(digits=(16, 2))
    older = fields.Float(digits=(16, 2))


class AgedPartnerBalanceMoveLine(models.TransientModel):

    _name = 'report_aged_partner_balance_qweb_move_line'

    report_partner_id = fields.Many2one(
        comodel_name='report_aged_partner_balance_qweb_partner',
        ondelete='cascade',
        index=True
    )
    move_line_id = fields.Many2one('account.move.line')
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

    _inherit = 'report_aged_partner_balance_qweb'

    @api.model
    def print_report(self):
        self.ensure_one()
        self.compute_data_for_report()
        return {
            'type': 'ir.actions.report.xml',
            'report_name':
                'account_financial_report_qweb.'
                'report_aged_partner_balance_qweb',
            'datas': {'ids': [self.id]},
        }

    @api.model
    def compute_data_for_report(self):
        self.ensure_one()
        model = self.env['report_open_invoice_qweb']
        self.open_invoice_id = model.create({
            'date_at': self.date_at,
            'only_posted_moves': self.only_posted_moves,
            'company_id': self.company_id.id,
            'filter_account_ids': [(6, 0, self.filter_account_ids.ids)],
            'filter_partner_ids': [(6, 0, self.filter_partner_ids.ids)],
        })
        self.open_invoice_id.compute_data_for_report()

        self.inject_account_values()
        self.inject_partner_values()
        self.inject_line_values()
        self.inject_line_values(only_empty_partner_line=True)
        if self.show_move_line_details:
            self.inject_move_line_values()
            self.inject_move_line_values(only_empty_partner_line=True)
        self.compute_accounts_cumul()

    def inject_account_values(self):
        query_inject_account = """
INSERT INTO
    report_aged_partner_balance_qweb_account
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
    report_open_invoice_qweb_account rao
WHERE
    rao.report_id = %s
        """
        query_inject_account_params = (
            self.id,
            self.env.uid,
            self.open_invoice_id.id,
        )
        self.env.cr.execute(query_inject_account, query_inject_account_params)

    def inject_partner_values(self):
        query_inject_partner = """
INSERT INTO
    report_aged_partner_balance_qweb_partner
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
    report_open_invoice_qweb_partner rpo
INNER JOIN
    report_open_invoice_qweb_account rao ON rpo.report_account_id = rao.id
INNER JOIN
    report_aged_partner_balance_qweb_account ra ON rao.code = ra.code
WHERE
    rao.report_id = %s
AND ra.report_id = %s
        """
        query_inject_partner_params = (
            self.env.uid,
            self.open_invoice_id.id,
            self.id,
        )
        self.env.cr.execute(query_inject_partner, query_inject_partner_params)

    def inject_line_values(self, only_empty_partner_line=False):
        query_inject_line = """
WITH
    date_range AS
        (
            SELECT
                %s AS date_current,
                DATE %s - INTEGER '30' AS date_less_30_days,
                DATE %s - INTEGER '60' AS date_less_60_days,
                DATE %s - INTEGER '90' AS date_less_90_days,
                DATE %s - INTEGER '120' AS date_less_120_days,
                DATE %s - INTEGER '150' AS date_older
        )
INSERT INTO
    report_aged_partner_balance_qweb_line
    (
        report_partner_id,
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
    rp.name,
    SUM(rlo.amount_residual) AS amount_residual,
    SUM(
        CASE
            WHEN rlo.date_due > date_range.date_less_30_days
            THEN rlo.amount_residual
        END
    ) AS current,
    SUM(
        CASE
            WHEN
                rlo.date_due > date_range.date_less_60_days
                AND rlo.date_due <= date_range.date_less_30_days
            THEN rlo.amount_residual
        END
    ) AS age_30_days,
    SUM(
        CASE
            WHEN
                rlo.date_due > date_range.date_less_90_days
                AND rlo.date_due <= date_range.date_less_60_days
            THEN rlo.amount_residual
        END
    ) AS age_60_days,
    SUM(
        CASE
            WHEN
                rlo.date_due > date_range.date_less_120_days
                AND rlo.date_due <= date_range.date_less_90_days
            THEN rlo.amount_residual
        END
    ) AS age_90_days,
    SUM(
        CASE
            WHEN
                rlo.date_due > date_range.date_older
                AND rlo.date_due <= date_range.date_less_120_days
            THEN rlo.amount_residual
        END
    ) AS age_120_days,
    SUM(
        CASE
            WHEN rlo.date_due <= date_range.date_older
            THEN rlo.amount_residual
        END
    ) AS older
FROM
    date_range,
    report_open_invoice_qweb_move_line rlo
INNER JOIN
    report_open_invoice_qweb_partner rpo ON rlo.report_partner_id = rpo.id
INNER JOIN
    report_open_invoice_qweb_account rao ON rpo.report_account_id = rao.id
INNER JOIN
    report_aged_partner_balance_qweb_account ra ON rao.code = ra.code
INNER JOIN
    report_aged_partner_balance_qweb_partner rp
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
        query_inject_line_params = (self.date_at,) * 6
        query_inject_line_params += (
            self.open_invoice_id.id,
            self.id,
        )
        self.env.cr.execute(query_inject_line, query_inject_line_params)

    def inject_move_line_values(self, only_empty_partner_line=False):
        query_inject_move_line = """
WITH
    date_range AS
        (
            SELECT
                %s AS date_current,
                DATE %s - INTEGER '30' AS date_less_30_days,
                DATE %s - INTEGER '60' AS date_less_60_days,
                DATE %s - INTEGER '90' AS date_less_90_days,
                DATE %s - INTEGER '120' AS date_less_120_days,
                DATE %s - INTEGER '150' AS date_older
        )
INSERT INTO
    report_aged_partner_balance_qweb_move_line
    (
        report_partner_id,
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
    rlo.date,
    rlo.date_due,
    rlo.entry,
    rlo.journal,
    rlo.account,
    rlo.partner,
    rlo.label,
    rlo.amount_residual AS amount_residual,
    CASE
        WHEN rlo.date_due > date_range.date_less_30_days
        THEN rlo.amount_residual
    END AS current,
    CASE
        WHEN
            rlo.date_due > date_range.date_less_60_days
            AND rlo.date_due <= date_range.date_less_30_days
        THEN rlo.amount_residual
    END AS age_30_days,
    CASE
        WHEN
            rlo.date_due > date_range.date_less_90_days
            AND rlo.date_due <= date_range.date_less_60_days
        THEN rlo.amount_residual
    END AS age_60_days,
    CASE
        WHEN
            rlo.date_due > date_range.date_less_120_days
            AND rlo.date_due <= date_range.date_less_90_days
        THEN rlo.amount_residual
    END AS age_90_days,
    CASE
        WHEN
            rlo.date_due > date_range.date_older
            AND rlo.date_due <= date_range.date_less_120_days
        THEN rlo.amount_residual
    END AS age_120_days,
    CASE
        WHEN rlo.date_due <= date_range.date_older
        THEN rlo.amount_residual
    END AS older
FROM
    date_range,
    report_open_invoice_qweb_move_line rlo
INNER JOIN
    report_open_invoice_qweb_partner rpo ON rlo.report_partner_id = rpo.id
INNER JOIN
    report_open_invoice_qweb_account rao ON rpo.report_account_id = rao.id
INNER JOIN
    report_aged_partner_balance_qweb_account ra ON rao.code = ra.code
INNER JOIN
    report_aged_partner_balance_qweb_partner rp
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
        query_inject_move_line_params = (self.date_at,) * 6
        query_inject_move_line_params += (
            self.open_invoice_id.id,
            self.id,
        )
        self.env.cr.execute(query_inject_move_line,
                            query_inject_move_line_params)

    def compute_accounts_cumul(self):
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
                report_aged_partner_balance_qweb_line rl
            INNER JOIN
                report_aged_partner_balance_qweb_partner rp
                    ON rl.report_partner_id = rp.id
            INNER JOIN
                report_aged_partner_balance_qweb_account ra
                    ON rp.report_account_id = ra.id
            WHERE
                ra.report_id = %s
            GROUP BY
                ra.id
        )
UPDATE
    report_aged_partner_balance_qweb_account
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
