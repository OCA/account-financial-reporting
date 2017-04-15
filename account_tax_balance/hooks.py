# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
try:
    from openerp.addons.mail_tracking.hooks import column_add_with_value
except ImportError:
    column_add_with_value = False

_logger = logging.getLogger(__name__)


def store_field_move_type(cr):
    cr.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='account_move' and column_name='move_type';
        """
    )
    if not cr.fetchone():
        _logger.info('Adding column move_type to table account_move')
        cr.execute(
            """
            ALTER TABLE account_move
            ADD COLUMN move_type
            varchar(30);
            COMMENT ON COLUMN account_move.move_type IS
            'Move type';
            """)

    _logger.info('Computing field move_type on account.move')

    cr.execute(
        """
        UPDATE account_move am
        SET move_type = 'liquidity'
        WHERE am.id IN (SELECT aml.move_id
        FROM account_move_line aml
        INNER JOIN account_account acc
        ON acc.id = aml.account_id
        where aml.move_id = am.id
        and acc.internal_type ='liquidity')
        and am.move_type is null;
        """
    )

    cr.execute(
        """
        UPDATE account_move am
        SET move_type = 'payable'
        WHERE am.id IN (SELECT aml.move_id
        FROM account_move_line aml
        INNER JOIN account_account acc
        ON acc.id = aml.account_id
        where aml.move_id = am.id
        and acc.internal_type ='payable'
        group by aml.move_id
        having sum(aml.balance) < 0)
        and am.move_type is null;
        """
    )

    cr.execute(
        """
        UPDATE account_move am
        SET move_type = 'payable_refund'
        WHERE am.id IN (SELECT aml.move_id
        FROM account_move_line aml
        INNER JOIN account_account acc
        ON acc.id = aml.account_id
        where aml.move_id = am.id
        and acc.internal_type ='payable'
        group by aml.move_id
        having sum(aml.balance) >= 0)
        and am.move_type is null;
        """
    )

    cr.execute(
        """
        UPDATE account_move am
        SET move_type = 'receivable'
        WHERE am.id IN (SELECT aml.move_id
        FROM account_move_line aml
        INNER JOIN account_account acc
        ON acc.id = aml.account_id
        where aml.move_id = am.id
        and acc.internal_type ='receivable'
        group by aml.move_id
        having sum(aml.balance) > 0)
        and am.move_type is null;
        """
    )

    cr.execute(
        """
        UPDATE account_move am
        SET move_type = 'receivable_refund'
        WHERE am.id IN (SELECT aml.move_id
        FROM account_move_line aml
        INNER JOIN account_account acc
        ON acc.id = aml.account_id
        where aml.move_id = am.id
        and acc.internal_type ='receivable'
        group by aml.move_id
        having sum(aml.balance) <= 0)
        and am.move_type is null;
        """
    )

    cr.execute(
        """
        UPDATE account_move am
        SET move_type = 'other'
        WHERE am.move_type is null;
        """
    )


def pre_init_hook(cr):
    """
    The objective of this hook is to speed up the installation
    of the module on an existing Odoo instance.

    Without this script, if a database has a few hundred thousand
    journal entries, which is not unlikely, the update will take
    at least a few hours.
    """
    store_field_move_type(cr)
