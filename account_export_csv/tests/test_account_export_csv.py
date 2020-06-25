# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date
from dateutil import relativedelta
import base64

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

    def test_file_content(self):
        report_wizard = self.report_wizard.create({
            "date_start": "2000-01-01",
            "date_end": "2200-01-01",
        })
        report_wizard.action_manual_export_journal_entries()
        res = base64.decodestring(report_wizard.data)
        line_number = self.env["account.move.line"].search_count([])
        # check the number of lines in file: include header + EOF line
        self.assertEqual(len(res.decode().split("\r\n")), line_number + 2)
