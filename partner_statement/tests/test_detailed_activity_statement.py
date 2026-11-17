from odoo.tests.common import TransactionCase


class TestDetailedActivityStatement(TransactionCase):
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
        cls.partner = cls.env["res.partner"]
        cls.partner1 = cls.partner.create(
            {
                "name": "Wood Corner",
            }
        )
        cls.partner2 = cls.partner.create(
            {
                "name": "Deco Addict",
            }
        )
        cls.statement_model = cls.env[
            "report.partner_statement.detailed_activity_statement"
        ]

    def test_get_title_prior_lines_receivable(self):
        """Title for prior balance of receivable account."""
        title = self.statement_model._get_title(
            self.partner1,
            ending_date="2024-03-31",
            currency="USD",
            line_type="prior_lines",
            account_type="asset_receivable",
        )

        self.assertEqual(
            title,
            "Prior Balance up to 2024-03-31 in USD",
            "Title for prior balance of receivable account is incorrect.",
        )

    def test_get_title_ending_lines_supplier(self):
        """Title for ending balance of supplier account."""
        title = self.statement_model._get_title(
            self.partner2,
            ending_date="2024-04-30",
            currency="EUR",
            line_type="ending_lines",
            account_type="liability_payable",
        )

        self.assertEqual(
            title,
            "Supplier Ending Balance up to 2024-04-30 in EUR",
            "Title for ending balance of supplier account is incorrect.",
        )
