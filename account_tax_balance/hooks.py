# © 2020 Opener B.V. <https://opener.amsterdam>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging


def pre_init_hook(cr):
    """ Precreate move_type and fill with appropriate values to prevent
    a MemoryError when the ORM attempts to call its compute method on a large
    amount of preexisting moves. Note that the order of the mapping is
    important as one move can have move lines on accounts of multiple types
    and the move type is set in the order of precedence. """
    logger = logging.getLogger(__name__)
    logger.info('Add account_move.move_type column if it does not yet exist')
    cr.execute(
        "ALTER TABLE account_move ADD COLUMN IF NOT EXISTS move_type VARCHAR")
    cr.execute(
        """
        UPDATE account_move am SET move_type = 'liquidity'
        FROM account_move_line aml
        WHERE aml.account_id IN (
            SELECT id FROM account_account
            WHERE internal_type = 'liquidity')
        AND aml.move_id = am.id AND am.move_type IS NULL
        """)
    logger.info('%s move set to type liquidity', cr.rowcount)
    cr.execute(
        """
        UPDATE account_move am SET move_type = 'payable'
        FROM account_move_line aml
        WHERE aml.account_id IN (
            SELECT id FROM account_account
            WHERE internal_type = 'payable')
        AND aml.move_id = am.id AND am.move_type IS NULL
        AND aml.balance < 0
        """)
    logger.info('%s move set to type payable', cr.rowcount)
    cr.execute(
        """
        UPDATE account_move am SET move_type = 'payable_refund'
        FROM account_move_line aml
        WHERE aml.account_id IN (
            SELECT id FROM account_account
            WHERE internal_type = 'payable')
        AND aml.move_id = am.id AND am.move_type IS NULL
        AND aml.balance >= 0
        """)
    logger.info('%s move set to type payable_refund', cr.rowcount)
    cr.execute(
        """
        UPDATE account_move am SET move_type = 'receivable'
        FROM account_move_line aml
        WHERE aml.account_id IN (
            SELECT id FROM account_account
            WHERE internal_type = 'receivable')
        AND aml.move_id = am.id AND am.move_type IS NULL
        AND aml.balance > 0
        """)
    logger.info('%s move set to type receivable', cr.rowcount)
    cr.execute(
        """
        UPDATE account_move am SET move_type = 'receivable_refund'
        FROM account_move_line aml
        WHERE aml.account_id IN (
            SELECT id FROM account_account
            WHERE internal_type = 'receivable')
        AND aml.move_id = am.id AND am.move_type IS NULL
        AND aml.balance <= 0
        """)
    logger.info('%s move set to type receivable_refund', cr.rowcount)
    cr.execute(
        """
        UPDATE account_move am SET move_type = 'other'
        WHERE am.move_type IS NULL
        """)
    logger.info('%s move set to type other', cr.rowcount)
