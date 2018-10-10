# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAmlReportXlsx(TransactionCase):

    def setUp(self):
        super(TestAmlReportXlsx, self).setUp()
        ctx = {'xlsx_export': True}
        self.report = self.env['ir.actions.report.xml'].with_context(ctx)
        self.report_name = 'move.line.list.xls'
        inv = self.env.ref('l10n_generic_coa.demo_invoice_1')
        self.amls = inv.move_id.line_ids

    def test_aml_report_xlsx(self):
        report_xls = self.report.render_report(
            self.amls.ids, self.report_name, {})
        self.assertEqual(report_xls[1], 'xlsx')
