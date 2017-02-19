# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MisBudgetItem(models.Model):

    _inherit = 'mis.kpi.data'
    _name = 'mis.budget.item'
    _description = 'MIS Budget Item'
    _order = 'budget_id, date_from, seq1, seq2'

    budget_id = fields.Many2one(
        comodel_name='mis.budget',
        required=True,
        ondelete='cascade',
        index=True,
    )
    budget_date_from = fields.Date(
        related='budget_id.date_from',
        readonly=True,
    )
    budget_date_to = fields.Date(
        related='budget_id.date_to',
        readonly=True,
    )
    report_id = fields.Many2one(
        related='budget_id.report_id',
        readonly=True,
    )
    kpi_expression_id = fields.Many2one(
        domain="[('kpi_id.report_id', '=', report_id),"
               " ('kpi_id.budgetable', '=', True)]",
    )
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        domain="[('date_start', '>=', budget_date_from),"
               " ('date_end', '<=', budget_date_to)]",
        string='Date range',
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string="Analytic account",
    )

    @api.onchange('date_range_id')
    def _onchange_date_range(self):
        for rec in self:
            if rec.date_range_id:
                rec.date_from = rec.date_range_id.date_start
                rec.date_to = rec.date_range_id.date_end

    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        for rec in self:
            if rec.date_range_id:
                if rec.date_from != rec.date_range_id.date_start or \
                        rec.date_to != rec.date_range_id.date_end:
                    rec.date_range_id = False

    @api.constrains('date_range_id', 'date_from', 'date_to',
                    'budget_id', 'kpi_expression_id')
    def _check_dates(self):
        for rec in self:
            # date_from <= date_to
            if rec.date_from > rec.date_to:
                raise ValidationError(
                    _("%s start date must not be after end date") %
                    (rec.name,))
            # within budget dates
            if rec.date_from < rec.budget_date_from or \
                    rec.date_to > rec.budget_date_to:
                raise ValidationError(
                    _("%s is not within budget %s date range.") %
                    (rec.name, rec.budget_id.name))
            # overlaps
            sql = """
                SELECT
                    id
                FROM
                    mis_budget_item bi
                WHERE
                    DATERANGE(bi.date_from, bi.date_to, '[]') &&
                        DATERANGE(%s::date, %s::date, '[]')
                    AND bi.id != %s
                    AND bi.budget_id = %s
                    AND bi.kpi_expression_id = %s
                LIMIT 1
            """
            self.env.cr.execute(sql, (rec.date_from, rec.date_to, rec.id,
                                      rec.budget_id.id,
                                      rec.kpi_expression_id.id))
            res = self.env.cr.fetchall()
            if res:
                bi = self.browse(res[0][0])
                raise ValidationError(
                    _("%s overlaps %s in budget %s") %
                    (rec.name, bi.name, rec.budget_id.name))
