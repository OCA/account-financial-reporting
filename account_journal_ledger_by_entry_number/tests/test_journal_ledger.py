# © 2023 FactorLibre - Alejandro Ji Cheung <alejandro.jicheung@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo.fields import Date
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestJournalLedger(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.JournalLedgerReportWizard = cls.env["journal.ledger.report.wizard"]
        cls.JournalLedgerReport = cls.env[
            "report.account_financial_report.journal_ledger"
        ]
        cls.MoveObj = cls.env["account.move"]
        cls.company = cls.company_data["company"]
        cls.company.account_sale_tax_id = False
        cls.company.account_purchase_tax_id = False
        cls.journal_sale = cls.company_data["default_journal_sale"]
        cls.income_account = cls.company_data["default_account_revenue"]
        cls.receivable_account = cls.company_data["default_account_receivable"]
        today = datetime.today()
        cls.fy_date_start = Date.to_string(today.replace(month=1, day=1))
        cls.fy_date_end = Date.to_string(today.replace(month=12, day=31))
        cls.journal_sale = cls.company_data["default_journal_sale"]

    def _add_move(
        self,
        date,
        journal,
        receivable_debit,
        receivable_credit,
        income_debit,
        income_credit,
    ):
        move_name = "move name"
        move_vals = {
            "journal_id": journal.id,
            "date": date,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": move_name,
                        "debit": receivable_debit,
                        "credit": receivable_credit,
                        "account_id": self.receivable_account.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "name": move_name,
                        "debit": income_debit,
                        "credit": income_credit,
                        "account_id": self.income_account.id,
                    },
                ),
            ],
        }
        return self.MoveObj.create(move_vals)

    def test_entry_number_in_journal_ledger(self):
        today_date = Date.today()
        vals = {
            "date_from": self.fy_date_start,
            "date_to": self.fy_date_end,
            "company_id": self.company.id,
            "journal_ids": [(6, 0, self.journal_sale.ids)],
            "move_target": "all",
            "sort_option": "entry_number",
        }
        wiz = self.JournalLedgerReportWizard.create(vals)
        data = wiz._prepare_report_journal_ledger()

        move1 = self._add_move(today_date, self.journal_sale, 0, 100, 100, 0)
        move1.action_post()
        move1.entry_number = False
        self.assertFalse(move1.entry_number)

        move2 = self._add_move(today_date, self.journal_sale, 0, 100, 100, 0)
        move2.action_post()
        self.assertNotEqual(move2.entry_number, False)

        res_data = self.JournalLedgerReport._get_report_values(wiz, data)
        self.assertEqual(move1.name, res_data.get("Moves")[1].get("entry"))
        self.assertEqual(move2.entry_number, res_data.get("Moves")[0].get("entry"))

        moves_order = self.JournalLedgerReport._get_moves_order(
            wiz, self.journal_sale.ids
        )
        self.assertEqual("entry_number asc", moves_order)

        vals.update({"sort_option": "date"})
        wiz2 = self.JournalLedgerReportWizard.create(vals)
        moves_order2 = self.JournalLedgerReport._get_moves_order(
            wiz2, self.journal_sale.ids
        )
        self.assertEqual("date asc, name asc", moves_order2)
