# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date
from dateutil import relativedelta

from odoo.tests.common import TransactionCase
from odoo import fields


class TestAccountExportCsv(TransactionCase):

    def setUp(self):
        super(TestAccountExportCsv, self).setUp()
        self.report_wizard = self.env['account.csv.export']
        today_dt = date.today()
        next_month_date = today_dt + relativedelta.relativedelta(months=1)
        self.report_date_start = fields.Date.to_string(today_dt)
        self.report_date_end = fields.Date.to_string(next_month_date)

    def test_1(self):
        report_wizard = self.report_wizard.create({
            'date_start': self.report_date_start,
            'date_end': self.report_date_end
        })
        report_wizard.action_manual_export_account()

    def test_2(self):
        report_wizard = self.report_wizard.create({
            'date_start': self.report_date_start,
            'date_end': self.report_date_end
        })
        report_wizard.action_manual_export_analytic()

    def test_3(self):
        report_wizard = self.report_wizard.create({
            'date_start': self.report_date_start,
            'date_end': self.report_date_end
        })
        report_wizard.action_manual_export_journal_entries()
