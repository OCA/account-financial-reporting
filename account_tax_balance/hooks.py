# Copyright 2020 Opener B.V. <https://opener.amsterdam>
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging


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
    env.cr.execute(
        """
        UPDATE account_move am SET financial_type = 'liquidity'
        FROM account_move_line aml
        JOIN account_account aa ON aa.id = aml.account_id
        WHERE aml.move_id = am.id AND am.financial_type IS NULL
        AND aa.account_type IN ('asset_cash', 'liability_credit_card')
        """
    )
    logger.info("liquidity move set to type %s", env.cr.rowcount)
    # Same rule as _compute_financial_type: the net balance of the payable or
    # receivable lines gives the type, a zero balance falls back to move_type.
    for account_type, negative, positive in (
        ("liability_payable", "payable", "payable_refund"),
        ("asset_receivable", "receivable_refund", "receivable"),
    ):
        env.cr.execute(
            """
            UPDATE account_move am SET financial_type = CASE
                WHEN s.balance < 0 THEN %(negative)s
                WHEN s.balance > 0 THEN %(positive)s
                ELSE CASE am.move_type
                    WHEN 'out_invoice' THEN 'receivable'
                    WHEN 'out_receipt' THEN 'receivable'
                    WHEN 'out_refund' THEN 'receivable_refund'
                    WHEN 'in_invoice' THEN 'payable'
                    WHEN 'in_receipt' THEN 'payable'
                    WHEN 'in_refund' THEN 'payable_refund'
                    ELSE 'other'
                END
            END
            FROM (
                SELECT aml.move_id, SUM(aml.balance) AS balance
                FROM account_move_line aml
                JOIN account_account aa ON aa.id = aml.account_id
                WHERE aa.account_type = %(account_type)s
                GROUP BY aml.move_id
            ) s
            WHERE s.move_id = am.id AND am.financial_type IS NULL
            """,
            {"account_type": account_type, "negative": negative, "positive": positive},
        )
        logger.info("%s moves set to a type %s", account_type, env.cr.rowcount)
    env.cr.execute(
        "UPDATE account_move SET financial_type = 'other' WHERE financial_type IS NULL"
    )
    logger.info("other move set to type %s", env.cr.rowcount)
