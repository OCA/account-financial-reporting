# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import openerp.tests.common as common


class TestMisBuilderBudget(common.TransactionCase):

    def setUp(self):
        super(TestMisBuilderBudget, self).setUp()
        self.inst_model = self.registry('mis.report.instance')

    def test_instance_01_compute(self):
        data = self.inst_model.compute(
            self.cr, self.uid,
            self.ref('mis_builder_budget.mis_report_instance_01'))
        kpi_01 = data['content'][0]
        val_r_comp = kpi_01['cols'][2]['val_r']
        self.assertIn('50', val_r_comp)
