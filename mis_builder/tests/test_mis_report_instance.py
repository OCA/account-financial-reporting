# -*- coding: utf-8 -*-
# © 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import openerp.tests.common as common
from openerp.tools import test_reports


class TestMisReportInstance(common.TransactionCase):
    """ Basic integration test to exercise mis.report.instance.

    We don't check the actual results here too much as computation correctness
    should be covered by lower level unit tests.
    """

    def setUp(self):
        super(TestMisReportInstance, self).setUp()
        partner_model_id = \
            self.env.ref('base.model_res_partner').id
        partner_create_date_field_id = \
            self.env.ref('base.field_res_partner_create_date').id
        partner_debit_field_id = \
            self.env.ref('account.field_res_partner_debit').id
        # create a report with 2 subkpis and one query
        self.report = self.env['mis.report'].create(dict(
            name='test report',
            subkpi_ids=[(0, 0, dict(
                name='sk1',
                description='subkpi 1',
                sequence=1,
            )), (0, 0, dict(
                name='sk2',
                description='subkpi 2',
                sequence=2,
            ))],
            query_ids=[(0, 0, dict(
                name='partner',
                model_id=partner_model_id,
                field_ids=[(4, partner_debit_field_id, None)],
                date_field=partner_create_date_field_id,
                aggregate='sum',
            ))],
        ))
        # kpi with accounting formulas
        self.env['mis.report.kpi'].create(dict(
            report_id=self.report.id,
            description='kpi 1',
            name='k1',
            multi=True,
            expression_ids=[(0, 0, dict(
                name='bale[200%]',
                subkpi_id=self.report.subkpi_ids[0].id,
            )), (0, 0, dict(
                name='balp[200%]',
                subkpi_id=self.report.subkpi_ids[1].id,
            ))],
        ))
        # kpi with accounting formula and query
        self.env['mis.report.kpi'].create(dict(
            report_id=self.report.id,
            description='kpi 2',
            name='k2',
            multi=True,
            expression_ids=[(0, 0, dict(
                name='balp[200%]',
                subkpi_id=self.report.subkpi_ids[0].id,
            )), (0, 0, dict(
                name='partner.debit',
                subkpi_id=self.report.subkpi_ids[1].id,
            ))],
        ))
        # kpi with a simple expression summing other multi-valued kpis
        self.env['mis.report.kpi'].create(dict(
            report_id=self.report.id,
            description='kpi 4',
            name='k4',
            multi=False,
            expression='k1 + k2 + k3',
        ))
        # kpi with 2 constants
        self.env['mis.report.kpi'].create(dict(
            report_id=self.report.id,
            description='kpi 3',
            name='k3',
            multi=True,
            expression_ids=[(0, 0, dict(
                name='AccountingNone',
                subkpi_id=self.report.subkpi_ids[0].id,
            )), (0, 0, dict(
                name='1.0',
                subkpi_id=self.report.subkpi_ids[1].id,
            ))],
        ))
        # kpi with a NameError (x not defined)
        self.env['mis.report.kpi'].create(dict(
            report_id=self.report.id,
            description='kpi 5',
            name='k5',
            multi=True,
            expression_ids=[(0, 0, dict(
                name='x',
                subkpi_id=self.report.subkpi_ids[0].id,
            )), (0, 0, dict(
                name='1.0',
                subkpi_id=self.report.subkpi_ids[1].id,
            ))],
        ))
        # create a report instance
        self.report_instance = self.env['mis.report.instance'].create(dict(
            name='test instance',
            report_id=self.report.id,
            company_id=self.env.ref('base.main_company').id,
            period_ids=[(0, 0, dict(
                name='p1',
                mode='relative',
                type='d',
                subkpi_ids=[(4, self.report.subkpi_ids[0].id, None)],
            )), (0, 0, dict(
                name='p2',
                mode='fix',
                manual_date_from='2014-01-01',
                manual_date_to='2014-12-31',
            ))],
        ))
        self.report_instance.period_ids[1].comparison_column_ids = \
            [(4, self.report_instance.period_ids[0].id, None)]

    def test_json(self):
        self.report_instance.compute()

    def test_qweb(self):
        test_reports.try_report(self.env.cr, self.env.uid,
                                'mis_builder.report_mis_report_instance',
                                [self.report_instance.id],
                                report_type='qweb-pdf')

    def test_xlsx(self):
        test_reports.try_report(self.env.cr, self.env.uid,
                                'mis.report.instance.xlsx',
                                [self.report_instance.id],
                                report_type='xlsx')
