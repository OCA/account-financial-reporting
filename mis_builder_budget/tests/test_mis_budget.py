# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase

from odoo.addons.mis_builder.tests.common import assert_matrix

from ..models.mis_report_instance_period import SRC_MIS_BUDGET


class TestMisBudget(TransactionCase):

    def setUp(self):
        super(TestMisBudget, self).setUp()
        # create report
        self.report = self.env['mis.report'].create(dict(
            name='test report',
        ))
        self.kpi1 = self.env['mis.report.kpi'].create(dict(
            report_id=self.report.id,
            name='k1',
            description='kpi 1',
            expression='10',
            budgetable=True,
        ))
        self.expr1 = self.kpi1.expression_ids[0]
        self.kpi2 = self.env['mis.report.kpi'].create(dict(
            report_id=self.report.id,
            name='k2',
            description='kpi 2',
            expression='k1 + 1',
        ))
        # budget
        self.budget = self.env['mis.budget'].create(dict(
            name='the budget',
            report_id=self.report.id,
            date_from='2017-01-01',
            date_to='2017-12-31',
            item_ids=[
                (0, 0, dict(
                    kpi_expression_id=self.expr1.id,
                    date_from='2017-01-01',
                    date_to='2017-01-31',
                    amount=10,
                )),
                (0, 0, dict(
                    kpi_expression_id=self.expr1.id,
                    date_from='2017-02-01',
                    date_to='2017-02-28',
                    amount=20,
                ))
            ]
        ))
        # instance
        self.instance = self.env['mis.report.instance'].create(dict(
            name='test instance',
            report_id=self.report.id,
            comparison_mode=True,
        ))
        self.pact1 = self.env['mis.report.instance.period'].create(dict(
            name='pact1',
            report_instance_id=self.instance.id,
            manual_date_from='2017-01-01',
            manual_date_to='2017-01-31',
        ))
        self.pbud1 = self.env['mis.report.instance.period'].create(dict(
            name='pbud1',
            report_instance_id=self.instance.id,
            source=SRC_MIS_BUDGET,
            source_mis_budget_id=self.budget.id,
            manual_date_from='2017-01-01',
            manual_date_to='2017-01-31',
        ))
        self.pact2 = self.env['mis.report.instance.period'].create(dict(
            name='pact2',
            report_instance_id=self.instance.id,
            manual_date_from='2017-02-01',
            manual_date_to='2017-02-28',
        ))
        self.pbud2 = self.env['mis.report.instance.period'].create(dict(
            name='pbud2',
            report_instance_id=self.instance.id,
            source=SRC_MIS_BUDGET,
            source_mis_budget_id=self.budget.id,
            manual_date_from='2017-02-01',
            manual_date_to='2017-02-21',
        ))

    def test1(self):
        matrix = self.instance._compute_matrix()
        assert_matrix(matrix, [
            # jan, bud jan, feb (3w), bud feb (3w),
            [10, 10, 10, 15],  # k1
            [11, 11, 11, 16],  # k2 = k1 = 1
        ])

    def test_drilldown(self):
        act = self.instance.drilldown(dict(
            period_id=self.pbud1.id,
            expr_id=self.expr1.id,
        ))
        assert act['res_model'] == 'mis.budget.item'
        assert act['domain'] == [
            ('date_from', '<=', '2017-01-31'),
            ('date_to', '>=', '2017-01-01'),
            ('kpi_expression_id', '=', self.expr1.id),
            ('budget_id', '=', self.budget.id),
        ]

    def test_copy(self):
        budget2 = self.budget.copy()
        assert len(budget2.item_ids) == len(self.budget.item_ids)

    def test_workflow(self):
        assert self.budget.state == 'draft'
        self.budget.action_confirm()
        assert self.budget.state == 'confirmed'
        self.budget.action_cancel()
        assert self.budget.state == 'cancelled'
        self.budget.action_draft()
        assert self.budget.state == 'draft'

    def test_name_search(self):
        report2 = self.report.copy()
        report2.kpi_ids[0].name = 'k1_1'
        budget2 = self.budget.copy()
        budget2.report_id = report2.id
        expr = self.env['mis.report.kpi.expression'].\
            with_context(default_budget_id=budget2.id).\
            name_search('k1')
        # search was restricted to the context of budget2
        # hence we found only k1_1 in report2 and not k1
        assert len(expr) == 1
        assert expr[0][1] == 'k1_1'
