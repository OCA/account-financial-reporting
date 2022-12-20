# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).-
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    analytic_account_ids = fields.Many2many(
        "account.analytic.account", compute="_compute_analytic_account_ids", store=True
    )

    @api.depends("analytic_distribution")
    def _compute_analytic_account_ids(self):
        for record in self:
            if not record.analytic_distribution:
                record.analytic_account_ids = False
            else:
                record.update(
                    {
                        "analytic_account_ids": [
                            (6, 0, [int(k) for k in record.analytic_distribution])
                        ]
                    }
                )

    def init(self):
        """
            The join between accounts_partners subquery and account_move_line
            can be heavy to compute on big databases.
            Join sample:
                JOIN
                    account_move_line ml
                        ON ap.account_id = ml.account_id
                        AND ml.date < '2018-12-30'
                        AND ap.partner_id = ml.partner_id
                        AND ap.include_initial_balance = TRUE
            By adding the following index, performances are strongly increased.
        :return:
        """
        self._cr.execute(
            "SELECT indexname FROM pg_indexes WHERE indexname = " "%s",
            ("account_move_line_account_id_partner_id_index",),
        )
        if not self._cr.fetchone():
            self._cr.execute(
                """
            CREATE INDEX account_move_line_account_id_partner_id_index
            ON account_move_line (account_id, partner_id)"""
            )

    @api.model
    def search_count(self, domain, limit=None):
        # In Big DataBase every time you change the domain widget this method
        # takes a lot of time. This improves performance
        if self.env.context.get("skip_search_count"):
            return 0
        return super().search_count(domain, limit=limit)
