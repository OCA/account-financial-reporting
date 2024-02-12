# Copyright 2020 Opener B.V. <https://opener.amsterdam>
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from psycopg2 import sql


def pre_init_hook(env):
    """Precreate financial_type and fill with appropriate values to prevent
    a MemoryError when the ORM attempts to call its compute method on a large
    amount of preexisting moves. Note that the order of the mapping is
    important as one move can have move lines on accounts of multiple types
    and the move type is set in the order of precedence."""
    logger = logging.getLogger(__name__)
    logger.info("Add account_move.financial_type column if it does not yet exist")
    env.cr.execute(
        "ALTER TABLE account_move ADD COLUMN IF NOT EXISTS financial_type VARCHAR"
    )
    MAPPING = [
        ("liquidity", "asset_cash", False),
        ("liquidity", "liability_credit_card", False),
        ("payable", "liability_payable", "AND aml.balance < 0"),
        ("payable_refund", "liability_payable", "AND aml.balance >= 0"),
        ("receivable", "asset_receivable", "AND aml.balance > 0"),
        ("receivable_refund", "asset_receivable", "AND aml.balance <= 0"),
        ("other", False, False),
    ]
    for financial_type, account_type, extra_where in MAPPING:
        args = [financial_type]
        query = sql.SQL("UPDATE account_move am SET financial_type = %s")
        if account_type:
            query += sql.SQL(
                """FROM account_move_line aml
                WHERE aml.account_id IN (
                    SELECT id FROM account_account
                    WHERE account_type = %s)
                AND aml.move_id = am.id AND am.financial_type IS NULL
                """
            )
            args.append(account_type)
        else:
            query += sql.SQL("WHERE am.financial_type IS NULL")
        if extra_where:
            query += sql.SQL(extra_where)
        env.cr.execute(query, tuple(args))
        logger.info("%s move set to type %s", financial_type, env.cr.rowcount)
