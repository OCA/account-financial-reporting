# Copyright 2026 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import pytz

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """Create and fill the ``stock.move.date_done`` column with plain SQL.

    It's a stored computed field, so on databases with a lot of stock moves the ORM
    would launch a full recomputation of the table on install. Creating the column
    beforehand makes the ORM skip it, as it only marks for computation the columns
    that it has just created.
    """
    tz = env.context.get("tz") or env.user.tz or "UTC"
    if tz not in pytz.all_timezones_set:
        tz = "UTC"
    env.cr.execute("ALTER TABLE stock_move ADD COLUMN IF NOT EXISTS date_done date")
    env.cr.execute(
        """
        UPDATE stock_move sm
        SET date_done = (sp.date_done AT TIME ZONE 'UTC' AT TIME ZONE %s)::date
        FROM stock_picking sp
        WHERE sm.picking_id = sp.id AND sp.date_done IS NOT NULL
        """,
        (tz,),
    )
    _logger.info("Pre-computed %s stock.move effective dates", env.cr.rowcount)
