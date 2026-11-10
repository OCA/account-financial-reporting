# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo.exceptions import ValidationError
from odoo.fields import Date
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestCashFlow(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env["res.company"].create({"name": "TEST"})
        self.report = self.browse_ref("mis_builder_cash_flow.mis_instance_cash_flow")
        self.report.company_id = self.company
        self.bank_account = self.env["account.account"].create(
            {
                "company_id": self.company.id,
                "code": "TEST1",
                "name": "Bank account 01",
                "account_type": "asset_cash",
            }
        )
        self.bank_account_hide = self.env["account.account"].create(
            {
                "company_id": self.company.id,
                "code": "TEST2",
                "name": "Bank account 02",
                "account_type": "asset_cash",
                "hide_in_cash_flow": True,
            }
        )
        self.account = self.env["account.account"].create(
            {
                "company_id": self.company.id,
                "code": "TEST3",
                "name": "Account",
                "account_type": "asset_cash",
                "reconcile": True,
            }
        )
        self.journal = self.env["account.journal"].create(
            {
                "name": "Journal",
                "code": "JOURNAL",
                "company_id": self.company.id,
                "type": "general",
            }
        )

    def test_company_constrain(self):
        with self.assertRaises(ValidationError):
            self.env["mis.cash_flow.forecast_line"].create(
                {"account_id": self.account.id, "date": Date.today(), "balance": 1000}
            )

    def test_report_instance(self):
        self.check_matrix()
        move = self.env["account.move"].create(
            {
                "name": "Move",
                "journal_id": self.journal.id,
                "company_id": self.company.id,
                "move_type": "entry",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.bank_account.id,
                            "debit": 1500,
                            "credit": 0,
                            "company_id": self.company.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.bank_account_hide.id,
                            "debit": 500,
                            "credit": 0,
                            "company_id": self.company.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.account.id,
                            "debit": 0,
                            "credit": 2000,
                            "company_id": self.company.id,
                        },
                    ),
                ],
            }
        )
        move._post()
        self.check_matrix(
            args=[
                ("liquidity", "Current", 1500),
                ("balance", "Current", 1500),
                ("in_receivable", "Current", -2000),
            ],
            ignore_rows=["balance", "period_balance", "in_total"],
        )
        date = Date.today() + timedelta(weeks=8)
        self.env["mis.cash_flow.forecast_line"].create(
            {
                "account_id": self.account.id,
                "date": date,
                "balance": 1000,
                "company_id": self.company.id,
            }
        )
        self.check_matrix(
            [
                ("liquidity", "Current", 1500),
                ("balance", "Current", 1500),
                ("in_receivable", "Current", -2000),
                ("in_forecast", "+8w", 1000),
            ],
            ignore_rows=["balance", "period_balance", "in_total"],
        )

    def test_balance_includes_forecast_on_non_liquidity_account(self):
        """A forecast line booked on an account whose type is neither
        liquidity nor receivable/payable (e.g. a current asset such as
        "Invoices to be issued") must feed the progressive BALANCE row, just
        as it already feeds PERIOD BALANCE, so that BALANCE keeps continuity
        with PERIOD BALANCE.
        """
        accrual_account = self.env["account.account"].create(
            {
                "company_id": self.company.id,
                "code": "TEST4",
                "name": "Invoices to be issued",
                "account_type": "asset_current",
            }
        )
        date = Date.today() + timedelta(weeks=8)
        self.env["mis.cash_flow.forecast_line"].create(
            {
                "account_id": accrual_account.id,
                "date": date,
                "balance": 1000,
                "company_id": self.company.id,
            }
        )
        with mute_logger("odoo.addons.mis_builder.models.kpimatrix"):
            matrix = self.report._compute_matrix()
        values = {}
        for row in matrix.iter_rows():
            for cell in row.iter_cells():
                if not cell:
                    continue
                values[(row.kpi.name, cell.subcol.col.label)] = cell.val
        # The forecast feeds the period rows...
        self.assertEqual(values[("in_forecast", "+8w")], 1000)
        self.assertEqual(values[("period_balance", "+8w")], 1000)
        # ...so, with no prior movement, the progressive BALANCE at +8w must
        # equal it (continuity with PERIOD BALANCE). A missing cell means 0,
        # which is exactly the regression this guards against.
        self.assertEqual(values.get(("balance", "+8w"), 0.0), 1000)

    def check_matrix(self, args=None, ignore_rows=None):
        if not args:
            args = []
        if not ignore_rows:
            ignore_rows = []
        with mute_logger("odoo.addons.mis_builder.models.kpimatrix"):
            matrix = self.report._compute_matrix()
        for row in matrix.iter_rows():
            if row.kpi.name in ignore_rows:
                continue
            for cell in row.iter_cells():
                if not cell:
                    continue
                found = False
                label = cell.subcol.col.label
                for exp in args:
                    if exp[0] == row.kpi.name and exp[1] == label:
                        found = True
                        break
                if not found:
                    self.assertEqual(cell.val, 0)
