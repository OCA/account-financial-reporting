#  Copyright 2023 Tecnativa - Carolina Fernandez
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import common, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestAccountAgeReportConfiguration(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_age_report_config = cls.env[
            "account.age.report.configuration"
        ].create(
            {
                "name": "Intervals configuration",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "1-30",
                            "inferior_limit": 30,
                        },
                    ),
                ],
            }
        )

    def test_check_line_ids_constraint(self):
        with self.assertRaises(ValidationError):
            self.env["account.age.report.configuration"].create(
                {"name": "Interval configuration", "line_ids": False}
            )

    def test_unique_line_name_per_configuration(self):
        line_model = self.env["account.age.report.configuration.line"]
        values = {
            "name": "31-60",
            "inferior_limit": 60,
            "account_age_report_config_id": self.account_age_report_config.id,
        }
        line_model.create(values)
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            line_model.create(values)

    def test_check_lower_inferior_limit_constraint(self):
        with self.assertRaises(ValidationError):
            self.account_age_report_config.line_ids.inferior_limit = 0

        with self.assertRaises(ValidationError):
            self.account_age_report_config.line_ids.inferior_limit = -1
