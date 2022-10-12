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

        self.statement_model = self.env["report.partner_statement.current_statement"]
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

    def test_customer_current_statement(self):

        wiz_id = self.wiz.with_context(
            active_ids=[self.partner1.id, self.partner2.id]
        ).create({})
        wiz_id.aging_type = "months"

        statement = wiz_id.button_export_pdf()

        self.assertDictContainsSubset(
            {
                "type": "ir.actions.report",
                "report_name": self.report_name,
                "report_type": "qweb-pdf",
            },
            statement,
            "There was an error and the PDF report was not generated.",
        )

        statement_xlsx = wiz_id.button_export_xlsx()

        self.assertDictContainsSubset(
            {
                "type": "ir.actions.report",
                "report_name": self.report_name_xlsx,
                "report_type": "xlsx",
            },
            statement_xlsx,
            "There was an error and the XLSX report was not generated.",
        )

        data = wiz_id._prepare_statement()
        self.assertIsInstance(
            data, dict, "There is an error while preparing the statement"
        )
        docids = data["partner_ids"]
        report = self.statement_model._get_report_values(docids, data)
        self.assertIsInstance(
            report, dict, "There was an error while compiling the report."
        )
        self.assertIn(
            "bucket_labels", report, "There was an error while compiling the report."
        )

    def test_customer_current_report_no_wizard(self):
        docids = [self.partner1.id]
        report = self.statement_model._get_report_values(docids, False)
        self.assertIsInstance(
            report, dict, "There was an error while compiling the report."
        )
        self.assertIn(
            "bucket_labels", report, "There was an error while compiling the report."
        )

    def test_customer_current_report_display_lines_sql_q1(self):
        docids = [self.partner1.id]
        query = self.statement_model._display_lines_sql_q1(
            docids, self.date_end, self.account_type
        )
        self.assertIsInstance(
            query, str, "There was an error while running _display_lines_sql_q1."
        )

    def test_customer_current_report_display_lines_sql_q2(self):
        query = self.statement_model._display_lines_sql_q2()
        self.assertIsInstance(
            query, str, "There was an error while running _display_lines_sql_q2."
        )

    def test_customer_display_lines_sql_q3(self):
        query = self.statement_model._display_lines_sql_q3(self.company.id)
        self.assertIsInstance(
            query, str, "There was an error while running _display_lines_sql_q3."
        )

    def test_get_account_display_lines(self):
        docids = [self.partner1.id]
        result = self.statement_model._get_account_display_lines(
            self.company.id, docids, self.date_start, self.date_end, self.account_type
        )
        self.assertIsInstance(
            result, dict, "There was an error while running _get_account_display_lines."
        )
