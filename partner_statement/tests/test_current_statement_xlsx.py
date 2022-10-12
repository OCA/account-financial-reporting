from odoo.tests.common import TransactionCase


class TestCurrentStatement(TransactionCase):
    """Tests for Current Statement."""

    def setUp(self):
        super().setUp()

        self.res_users_model = self.env["res.users"]
        self.company = self.env.ref("base.main_company")
        self.company.external_report_layout_id = self.env.ref(
            "web.external_layout_standard"
        )
        self.partner1 = self.env.ref("base.res_partner_2")
        self.partner2 = self.env.ref("base.res_partner_3")
        self.g_account_user = self.env.ref("account.group_account_user")

        self.user = self._create_user("user_1", [self.g_account_user], self.company).id

        # self.statement_model = self.env["report.partner_statement.current_statement"]
        self.statement_xlsx_model = self.env["report.p_s.report_current_statement_xlsx"]
        self.wiz = self.env["current.statement.wizard"]
        self.report_name = "partner_statement.current_statement"
        self.report_name_xlsx = "p_s.report_current_statement_xlsx"
        self.report_title = "Current Statement"
        self.date_end = "2022-09-30"
        self.date_start = "2022-09-01"
        self.account_type = "receivable"
        self.show_aging_buckets = True
        self.filter_partners_non_due = False
        self.aging_type = "days"
        self.filter_negative_balances = False

    def _create_user(self, login, groups, company):
        group_ids = [group.id for group in groups]
        user = self.res_users_model.create(
            {
                "name": login,
                "login": login,
                "email": "example@yourcompany.com",
                "company_id": company.id,
                "company_ids": [(4, company.id)],
                "groups_id": [(6, 0, group_ids)],
            }
        )
        return user

    def test_get_report_name(self):
        test_data = {
            "date_end": self.date_end,
            "company_id": self.company.id,
            "partner_ids": [self.partner1],
            "show_aging_buckets": self.show_aging_buckets,
            "filter_non_due_partners": self.filter_partners_non_due,
            "account_type": self.account_type,
            "aging_type": self.aging_type,
            "filter_negative_balances": self.filter_negative_balances,
        }
        result = self.statement_xlsx_model._get_report_name(None, test_data)
        self.assertIsInstance(
            result, str, "There was an error while running _get_report_name_xlsx."
        )
