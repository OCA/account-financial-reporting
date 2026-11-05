# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase, users


class TestResConfigSettings(TransactionCase):
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
        cls.config = cls.env["res.config.settings"]
        user = cls.env["res.users"].create(
            {
                "name": "Account Test User",
                "login": "account_test",
                "email": "account_test@example.com",
                "group_ids": [
                    (6, 0, [cls.env.ref("account.group_account_invoice").id])
                ],
            }
        )
        cls.account_user = user.id
        cls.user_obj = cls.env["res.users"].with_user(cls.account_user)

    @users("admin")
    def test_groups(self):
        conf = self.config.create(
            {
                "default_aging_type": "months",
                "group_activity_statement": True,
                "group_outstanding_statement": False,
            }
        )
        conf.set_values()
        self.admin_user = self.env.ref("base.user_admin")
        self.assertFalse(
            self.admin_user._has_group("partner_statement.group_outstanding_statement")
        )
        self.assertTrue(
            self.admin_user._has_group("partner_statement.group_activity_statement")
        )
        res = (
            self.env["activity.statement.wizard"]
            .with_context(active_ids=[1])
            .create({})
        )
        self.assertEqual(res.aging_type, "months")
