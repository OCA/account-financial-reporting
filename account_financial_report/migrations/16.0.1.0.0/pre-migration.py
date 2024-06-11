# Copyright 2024 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Pre-create analytic_account_ids m2m relation and pre-fill it"""
    env.cr.execute(
        """
        CREATE TABLE account_analytic_account_account_move_line_rel (
            account_move_line_id INTEGER NOT NULL,
            account_analytic_account_id INTEGER NOT NULL,
            PRIMARY KEY(account_move_line_id, account_analytic_account_id)
        );
        COMMENT ON TABLE account_analytic_account_account_move_line_rel IS
            'RELATION BETWEEN account_move_line AND account_analytic_account';
        CREATE INDEX ON account_analytic_account_account_move_line_rel (
            account_analytic_account_id,account_move_line_id
        );
    """
    )
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO account_analytic_account_account_move_line_rel (
            account_move_line_id, account_analytic_account_id
        )
        SELECT
            aml.id AS account_move_line_id,
            jsonb_each.key::int AS account_analytic_account_id
        FROM
            account_move_line aml,
            jsonb_each(aml.analytic_distribution) AS jsonb_each
        WHERE
            aml.analytic_distribution IS NOT NULL;
    """,
    )
