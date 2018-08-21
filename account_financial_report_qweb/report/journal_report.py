# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

DIGITS = (16, 2)


class ReportJournalQweb(models.TransientModel):

    _name = 'report_journal_qweb'
    _inherit = 'report_qweb_abstract'

    date_from = fields.Date(
        required=True
    )
    date_to = fields.Date(
        required=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True,
        ondelete='cascade'
    )
    move_target = fields.Selection(
        selection='_get_move_targets',
        default='all',
        required=True,
    )
    sort_option = fields.Selection(
        selection='_get_sort_options',
        default='move_name',
        required=True,
    )
    group_option = fields.Selection(
        selection='_get_group_options',
        default='journal',
        required=True,
    )
    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        required=True,
    )
    report_journal_ids = fields.One2many(
        comodel_name='report_journal_qweb_journal',
        inverse_name='report_id',
    )
    report_move_ids = fields.One2many(
        comodel_name='report_journal_qweb_move',
        inverse_name='report_id',
    )
    report_move_line_ids = fields.One2many(
        comodel_name='report_journal_qweb_move_line',
        inverse_name='report_id',
    )
    report_journal_tax_line_ids = fields.One2many(
        comodel_name='report_journal_qweb_journal_tax_line',
        inverse_name='report_id',
    )
    report_tax_line_ids = fields.One2many(
        comodel_name='report_journal_qweb_report_tax_line',
        inverse_name='report_id',
    )
    foreign_currency = fields.Boolean()
    with_account_name = fields.Boolean()

    @api.model
    def _get_move_targets(self):
        return self.env['journal.report.wizard']._get_move_targets()

    @api.model
    def _get_sort_options(self):
        return self.env['journal.report.wizard']._get_sort_options()

    @api.model
    def _get_group_options(self):
        return self.env['journal.report.wizard']._get_group_options()

    @api.multi
    def refresh(self):
        self.ensure_one()
        self.report_journal_ids.unlink()
        self.compute_data_for_report()

    @api.multi
    def compute_data_for_report(self):
        self.ensure_one()
        self._inject_journal_values()
        self._inject_move_values()
        self._inject_move_line_values()
        self._inject_journal_tax_values()
        self._update_journal_report_total_values()

        if self.group_option == 'none':
            self._inject_report_tax_values()

        # Refresh cache because all data are computed with SQL requests
        self.invalidate_cache()

    @api.multi
    def _inject_journal_values(self):
        self.ensure_one()
        sql = """
            DELETE
            FROM report_journal_qweb_journal
            WHERE report_id = %s
        """
        params = (
            self.id,
        )
        self.env.cr.execute(sql, params)
        sql = """
            INSERT INTO report_journal_qweb_journal (
                create_uid,
                create_date,
                report_id,
                journal_id,
                name,
                code,
                company_id,
                currency_id
            )
            SELECT
                %s as create_uid,
                NOW() as create_date,
                %s as report_id,
                aj.id as journal_id,
                aj.name as name,
                aj.code as code,
                aj.company_id as company_id,
                COALESCE(aj.currency_id, company.currency_id) as currency_id
            FROM
                account_journal aj
            LEFT JOIN
                res_company company on (company.id = aj.company_id)
            WHERE
                aj.id in %s
            AND
                aj.company_id = %s
            ORDER BY
                aj.name
        """
        params = (
            self.env.uid,
            self.id,
            tuple(self.journal_ids.ids),
            self.company_id.id,
        )
        self.env.cr.execute(sql, params)

    @api.multi
    def _inject_move_values(self):
        self.ensure_one()
        sql = """
            DELETE
            FROM report_journal_qweb_move
            WHERE report_id = %s
        """
        params = (
            self.id,
        )
        self.env.cr.execute(sql, params)
        sql = self._get_inject_move_insert()
        sql += self._get_inject_move_select()
        sql += self._get_inject_move_where_clause()
        sql += self._get_inject_move_order_by()
        params = self._get_inject_move_params()
        self.env.cr.execute(sql, params)

    @api.multi
    def _get_inject_move_insert(self):
        return """
            INSERT INTO report_journal_qweb_move (
                create_uid,
                create_date,
                report_id,
                report_journal_id,
                move_id,
                name,
                company_id
            )
        """

    @api.multi
    def _get_inject_move_select(self):
        return """
            SELECT
                %s as create_uid,
                NOW() as create_date,
                rjqj.report_id as report_id,
                rjqj.id as report_journal_id,
                am.id as move_id,
                am.name as name,
                am.company_id as company_id
            FROM
                account_move am
            INNER JOIN
                report_journal_qweb_journal rjqj
                    on (rjqj.journal_id = am.journal_id)
        """

    @api.multi
    def _get_inject_move_where_clause(self):
        self.ensure_one()
        where_clause = """
            WHERE
                rjqj.report_id = %s
            AND
                am.date >= %s
            AND
                am.date <= %s
        """
        if self.move_target != 'all':
            where_clause += """
                AND
                    am.state = %s
            """
        return where_clause

    @api.multi
    def _get_inject_move_order_by(self):
        self.ensure_one()
        order_by = """
            ORDER BY
        """
        if self.sort_option == 'move_name':
            order_by += " am.name"
        elif self.sort_option == 'date':
            order_by += " am.date, am.name"
        return order_by

    @api.multi
    def _get_inject_move_params(self):
        params = [
            self.env.uid,
            self.id,
            self.date_from,
            self.date_to
        ]

        if self.move_target != 'all':
            params.append(self.move_target)

        return tuple(params)

    @api.multi
    def _inject_move_line_values(self):
        self.ensure_one()
        sql = """
            DELETE
            FROM report_journal_qweb_move_line
            WHERE report_id = %s
        """
        params = (
            self.id,
        )
        self.env.cr.execute(sql, params)
        sql = """
            INSERT INTO report_journal_qweb_move_line (
                create_uid,
                create_date,
                report_id,
                report_journal_id,
                report_move_id,
                move_line_id,
                account_id,
                account,
                account_code,
                account_type,
                partner_id,
                partner,
                date,
                entry,
                label,
                debit,
                credit,
                company_currency_id,
                amount_currency,
                currency_id,
                currency_name,
                tax_id,
                taxes_description,
                company_id
            )
            SELECT
                %s as create_uid,
                NOW() as create_date,
                rjqm.report_id as report_id,
                rjqm.report_journal_id as report_journal_id,
                rjqm.id as report_move_id,
                aml.id as move_line_id,
                aml.account_id as account_id,
                aa.name as account,
                aa.code as account_code,
                aa.internal_type as account_type,
                aml.partner_id as partner_id,
                p.name as partner,
                aml.date as date,
                rjqm.name as entry,
                aml.name as label,
                aml.debit as debit,
                aml.credit as credit,
                aml.company_currency_id as currency_id,
                aml.amount_currency as amount_currency,
                aml.currency_id as currency_id,
                currency.name as currency_name,
                aml.tax_line_id as tax_id,
                CASE
                    WHEN
                      aml.tax_line_id is not null
                THEN
                    COALESCE(at.description, at.name)
                WHEN
                    aml.tax_line_id is null
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
                        aml_at_rel.account_move_line_id = aml.id)
                ELSE
                    ''
                END as taxes_description,
                aml.company_id as company_id
            FROM
                account_move_line aml
            INNER JOIN
                report_journal_qweb_move rjqm
                    on (rjqm.move_id = aml.move_id)
            LEFT JOIN
                account_account aa
                    on (aa.id = aml.account_id)
            LEFT JOIN
                res_partner p
                    on (p.id = aml.partner_id)
            LEFT JOIN
                account_tax at
                    on (at.id = aml.tax_line_id)
            LEFT JOIN
                res_currency currency
                    on (currency.id = aml.currency_id)
            WHERE
                rjqm.report_id = %s
        """
        params = (
            self.env.uid,
            self.id,
        )
        self.env.cr.execute(sql, params)

    @api.multi
    def _inject_report_tax_values(self):
        self.ensure_one()
        sql_distinct_tax_id = """
            SELECT
                distinct(jrqjtl.tax_id)
            FROM
                report_journal_qweb_journal_tax_line jrqjtl
            WHERE
                jrqjtl.report_id = %s
        """
        self.env.cr.execute(sql_distinct_tax_id, (self.id,))
        rows = self.env.cr.fetchall()
        tax_ids = set([row[0] for row in rows])

        sql = """
            INSERT INTO report_journal_qweb_report_tax_line (
                create_uid,
                create_date,
                report_id,
                tax_id,
                tax_name,
                tax_code,
                base_debit,
                base_credit,
                tax_debit,
                tax_credit
            )
            SELECT
                %s as create_uid,
                NOW() as create_date,
                %s as report_id,
                %s as tax_id,
                at.name as tax_name,
                at.description as tax_code,
                (
                    SELECT sum(base_debit)
                    FROM report_journal_qweb_journal_tax_line jrqjtl2
                    WHERE jrqjtl2.report_id = %s
                    AND jrqjtl2.tax_id = %s
                ) as base_debit,
                (
                    SELECT sum(base_credit)
                    FROM report_journal_qweb_journal_tax_line jrqjtl2
                    WHERE jrqjtl2.report_id = %s
                    AND jrqjtl2.tax_id = %s
                ) as base_credit,
                (
                    SELECT sum(tax_debit)
                    FROM report_journal_qweb_journal_tax_line jrqjtl2
                    WHERE jrqjtl2.report_id = %s
                    AND jrqjtl2.tax_id = %s
                ) as tax_debit,
                (
                    SELECT sum(tax_credit)
                    FROM report_journal_qweb_journal_tax_line jrqjtl2
                    WHERE jrqjtl2.report_id = %s
                    AND jrqjtl2.tax_id = %s
                ) as tax_credit
            FROM
                report_journal_qweb_journal_tax_line jrqjtl
            LEFT JOIN
                account_tax at
                    on (at.id = jrqjtl.tax_id)
            WHERE
                jrqjtl.report_id = %s
            AND
                jrqjtl.tax_id = %s
        """

        for tax_id in tax_ids:
            params = (
                self.env.uid,
                self.id,
                tax_id,
                self.id,
                tax_id,
                self.id,
                tax_id,
                self.id,
                tax_id,
                self.id,
                tax_id,
                self.id,
                tax_id,
            )
            self.env.cr.execute(sql, params)

    @api.multi
    def _inject_journal_tax_values(self):
        self.ensure_one()
        sql = """
            DELETE
            FROM report_journal_qweb_journal_tax_line
            WHERE report_id = %s
        """
        params = (
            self.id,
        )
        self.env.cr.execute(sql, params)
        sql_distinct_tax_id = """
            SELECT
                distinct(jrqml.tax_id)
            FROM
                report_journal_qweb_move_line jrqml
            WHERE
                jrqml.report_journal_id = %s
        """

        tax_ids_by_journal_id = {}
        for report_journal in self.report_journal_ids:
            if report_journal.id not in tax_ids_by_journal_id:
                tax_ids_by_journal_id[report_journal.id] = []
            self.env.cr.execute(sql_distinct_tax_id, (report_journal.id,))
            rows = self.env.cr.fetchall()
            tax_ids_by_journal_id[report_journal.id].extend([
                row[0] for row in rows if row[0]
            ])

        sql = """
            INSERT INTO report_journal_qweb_journal_tax_line (
                create_uid,
                create_date,
                report_id,
                report_journal_id,
                tax_id,
                tax_name,
                tax_code,
                base_debit,
                base_credit,
                tax_debit,
                tax_credit
            )
            SELECT
                %s as create_uid,
                NOW() as create_date,
                %s as report_id,
                %s as report_journal_id,
                %s as tax_id,
                at.name as tax_name,
                at.description as tax_code,
                (
                    SELECT sum(debit)
                    FROM report_journal_qweb_move_line jrqml2
                    WHERE jrqml2.report_journal_id = %s
                    AND (
                        SELECT
                            count(*)
                        FROM
                            account_move_line_account_tax_rel aml_at_rel
                        WHERE
                            aml_at_rel.account_move_line_id =
                                jrqml2.move_line_id
                        AND
                            aml_at_rel.account_tax_id = %s
                    ) > 0
                ) as base_debit,
                (
                    SELECT sum(credit)
                    FROM report_journal_qweb_move_line jrqml2
                    WHERE jrqml2.report_journal_id = %s
                    AND (
                        SELECT
                            count(*)
                        FROM
                            account_move_line_account_tax_rel aml_at_rel
                        WHERE
                            aml_at_rel.account_move_line_id =
                                jrqml2.move_line_id
                        AND
                            aml_at_rel.account_tax_id = %s
                    ) > 0
                ) as base_credit,
                (
                    SELECT sum(debit)
                    FROM report_journal_qweb_move_line jrqml2
                    WHERE jrqml2.report_journal_id = %s
                    AND jrqml2.tax_id = %s
                ) as tax_debit,
                (
                    SELECT sum(credit)
                    FROM report_journal_qweb_move_line jrqml2
                    WHERE jrqml2.report_journal_id = %s
                    AND jrqml2.tax_id = %s
                ) as tax_credit
            FROM
                report_journal_qweb_journal rjqj
            LEFT JOIN
                account_tax at
                    on (at.id = %s)
            WHERE
                rjqj.id = %s
        """

        for report_journal_id in tax_ids_by_journal_id:
            tax_ids = tax_ids_by_journal_id[report_journal_id]
            for tax_id in tax_ids:
                params = (
                    self.env.uid,
                    self.id,
                    report_journal_id,
                    tax_id,
                    report_journal_id,
                    tax_id,
                    report_journal_id,
                    tax_id,
                    report_journal_id,
                    tax_id,
                    report_journal_id,
                    tax_id,
                    tax_id,
                    report_journal_id,
                )
                self.env.cr.execute(sql, params)

    @api.multi
    def _update_journal_report_total_values(self):
        self.ensure_one()
        sql = """
            UPDATE
                report_journal_qweb_journal rjqj
            SET
                debit = (
                    SELECT sum(rjqml.debit)
                    FROM report_journal_qweb_move_line rjqml
                    WHERE rjqml.report_journal_id = rjqj.id
                ),
                credit = (
                    SELECT sum(rjqml.credit)
                    FROM report_journal_qweb_move_line rjqml
                    WHERE rjqml.report_journal_id = rjqj.id
                )
            WHERE
                rjqj.report_id = %s
        """
        self.env.cr.execute(sql, (self.id,))

    @api.multi
    def print_report(self, report_type):
        self.ensure_one()
        if report_type == 'xlsx':
            report_name = 'account_financial_report_qweb.' \
                          'report_journal_xlsx'
        else:
            report_name = 'account_financial_report_qweb.' \
                          'report_journal_qweb'
        return self.env['report'].get_action(
            docids=self.ids, report_name=report_name)

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'account_financial_report_qweb.'
                'report_journal_html').render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self._get_html()


class ReportJournalQwebJournal(models.TransientModel):

    _name = 'report_journal_qweb_journal'
    _inherit = 'report_qweb_abstract'

    name = fields.Char(
        required=True,
    )
    code = fields.Char()
    report_id = fields.Many2one(
        comodel_name='report_journal_qweb',
        required=True,
        ondelete='cascade'
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        required=True,
        ondelete='cascade',
    )
    report_move_ids = fields.One2many(
        comodel_name='report_journal_qweb_move',
        inverse_name='report_journal_id',
    )
    report_tax_line_ids = fields.One2many(
        comodel_name='report_journal_qweb_journal_tax_line',
        inverse_name='report_journal_id',
    )
    debit = fields.Float(
        digits=DIGITS,
    )
    credit = fields.Float(
        digits=DIGITS,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True,
        ondelete='cascade'
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
    )


class ReportJournalQwebMove(models.TransientModel):

    _name = 'report_journal_qweb_move'
    _inherit = 'report_qweb_abstract'

    report_id = fields.Many2one(
        comodel_name='report_journal_qweb',
        required=True,
        ondelete='cascade'
    )
    report_journal_id = fields.Many2one(
        comodel_name='report_journal_qweb_journal',
        required=True,
        ondelete='cascade',
    )
    move_id = fields.Many2one(
        comodel_name='account.move',
        required=True,
        ondelete='cascade',
    )
    report_move_line_ids = fields.One2many(
        comodel_name='report_journal_qweb_move_line',
        inverse_name='report_move_id',
    )
    name = fields.Char()
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True,
        ondelete='cascade'
    )


class ReportJournalQwebMoveLine(models.TransientModel):

    _name = 'report_journal_qweb_move_line'
    _inherit = 'report_qweb_abstract'
    _order = 'partner_id desc, account_id desc'

    report_id = fields.Many2one(
        comodel_name='report_journal_qweb',
        required=True,
        ondelete='cascade'
    )
    report_journal_id = fields.Many2one(
        comodel_name='report_journal_qweb_journal',
        required=True,
        ondelete='cascade',
    )
    report_move_id = fields.Many2one(
        comodel_name='report_journal_qweb_move',
        required=True,
        ondelete='cascade',
    )
    move_line_id = fields.Many2one(
        comodel_name='account.move.line',
        required=True,
        ondelete='cascade',
    )
    account_id = fields.Many2one(
        comodel_name='account.account'
    )
    account = fields.Char()
    account_code = fields.Char()
    account_type = fields.Char()
    partner = fields.Char()
    partner_id = fields.Many2one(
        comodel_name='res.partner',
    )
    date = fields.Date()
    entry = fields.Char()
    label = fields.Char()
    debit = fields.Float(
        digits=DIGITS,
    )
    credit = fields.Float(
        digits=DIGITS,
    )
    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
    )
    amount_currency = fields.Monetary(
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
    )
    currency_name = fields.Char()
    taxes_description = fields.Char()
    tax_id = fields.Many2one(
        comodel_name='account.tax'
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True,
        ondelete='cascade'
    )


class ReportJournalQwebReportTaxLine(models.TransientModel):

    _name = 'report_journal_qweb_report_tax_line'
    _inherit = 'report_qweb_abstract'
    _order = 'tax_code'

    report_id = fields.Many2one(
        comodel_name='report_journal_qweb',
        required=True,
        ondelete='cascade'
    )
    tax_id = fields.Many2one(
        comodel_name='account.tax'
    )
    tax_name = fields.Char()
    tax_code = fields.Char()
    base_debit = fields.Float(
        digits=DIGITS,
    )
    base_credit = fields.Float(
        digits=DIGITS,
    )
    base_balance = fields.Float(
        digits=DIGITS,
        compute='_compute_base_balance',
    )
    tax_debit = fields.Float(
        digits=DIGITS,
    )
    tax_credit = fields.Float(
        digits=DIGITS,
    )
    tax_balance = fields.Float(
        digits=DIGITS,
        compute='_compute_tax_balance'
    )

    @api.multi
    def _compute_base_balance(self):
        for rec in self:
            rec.base_balance = rec.base_debit - rec.base_credit

    @api.multi
    def _compute_tax_balance(self):
        for rec in self:
            rec.tax_balance = rec.tax_debit - rec.tax_credit


class ReportJournalQwebJournalTaxLine(models.TransientModel):

    _name = 'report_journal_qweb_journal_tax_line'
    _inherit = 'report_journal_qweb_report_tax_line'
    _order = 'tax_code'

    report_journal_id = fields.Many2one(
        comodel_name='report_journal_qweb_journal',
        required=True,
        ondelete='cascade',
    )
