# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .models.account_move_line import AccountMoveLine


def pre_init_hook(cr):
    with cr.savepoint():
        # don't break if column exists
        cr.execute(
            'alter table account_move_line add column last_rec_date date',
        )
        cr.execute(
            'comment on column account_move_line.last_rec_date is %s',
            (AccountMoveLine.last_rec_date.string,),
        )
        cr.execute(
            'create index account_move_line_last_rec_date_index '
            'on account_move_line (last_rec_date)',
        )
    # but still do the initialization
    cr.execute(
        """update account_move_line
        set last_rec_date=ml_fr.date
        from account_move_line ml
        left join account_move_reconcile fr on ml.reconcile_id=fr.id
        join (
            select
            coalesce(reconcile_id, reconcile_partial_id) as reconcile_id,
            max(date) as date
            from account_move_line
            group by coalesce(reconcile_id, reconcile_partial_id)
        ) ml_fr on ml_fr.reconcile_id=fr.id
        where ml.id=account_move_line.id"""
    )
