# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    _logger.info('Updating column last_rec_date on account_move_line')

    cr.execute(
        """
        UPDATE account_move_line SET last_rec_date = rec_data.aml_date
        FROM (
            SELECT rec.id, max(aml.date) as aml_date
            FROM account_move_line aml
            JOIN account_move_reconcile rec
            ON rec.id = aml.reconcile_id
            GROUP BY rec.id
        ) as rec_data
        WHERE rec_data.id = account_move_line.reconcile_id
        """
    )

    cr.execute(
        """
        UPDATE account_move_line SET last_rec_date = rec_data.aml_date
        FROM (
            SELECT rec.id, max(aml.date) as aml_date
            FROM account_move_line aml
            JOIN account_move_reconcile rec
            ON rec.id = aml.reconcile_partial_id
            GROUP BY rec.id
        ) as rec_data
        WHERE rec_data.id = account_move_line.reconcile_partial_id
        """
    )
