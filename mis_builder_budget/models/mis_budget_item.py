# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class MisBudgetItem(models.Model):

    _name = 'mis.budget.item'
    _description = 'MIS Budget Item'
    _order = 'budget_id, date_from'

    name = fields.Char(
        compute='_compute_name',
        required=False,
        readonly=True,
    )
    date_from = fields.Date(
        required=True,
        string="From",
    )
    date_to = fields.Date(
        required=True,
        string="To",
    )
    amount = fields.Float(
    )
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
    kpi_id = fields.Many2one(
        comodel_name='mis.report.kpi',
        required=True,
        ondelete='restrict',
        string="KPI",
        domain="[('report_id', '=', report_id),"
               " ('budgetable', '=', True)]",
    )
    period_id = fields.Many2one(
        comodel_name='account.period',
        domain="[('date_start', '>=', budget_date_from),"
               " ('date_stop', '<=', budget_date_to),"
               " ('special', '=', False)]",
        string='Period',
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string="Analytic account",
    )

    @api.depends('kpi_id.name',
                 'date_from',
                 'date_to')
    def _compute_name(self):
        for rec in self:
            rec.name = u'{}: {} - {}'.format(
                rec.kpi_id.name,
                rec.date_from,
                rec.date_to)

    @api.onchange('period_id')
    def _onchange_period_id(self):
        for rec in self:
            if rec.period_id:
                rec.date_from = rec.period_id.date_start
                rec.date_to = rec.period_id.date_stop

    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        for rec in self:
            if rec.period_id:
                if rec.date_from != rec.period_id.date_start or \
                        rec.date_to != rec.period_id.date_stop:
                    rec.period_id = False

    @api.multi
    def _prepare_overlap_domain(self):
        """Prepare a domain to check for overlapping budget items."""
        self.ensure_one()
        return [
            ('date_from', '<=', self.date_to),
            ('date_to', '>=', self.date_from),
            ('budget_id', '=', self.budget_id.id),
            ('kpi_id', '=', self.kpi_id.id),
            ('analytic_account_id', '=', self.analytic_account_id.id),
            ('id', '!=', self.id),
        ]

    @api.constrains('period_id', 'date_from', 'date_to', 'budget_id')
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
            domain = rec._prepare_overlap_domain()
            res = self.search(domain, limit=1)
            if res:
                raise ValidationError(
                    _("%s overlaps %s in budget %s") %
                    (rec.name, res.name, rec.budget_id.name))
