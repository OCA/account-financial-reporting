# Copyright 2020 Ozono Multimedia S.L.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade

field_renames = [
    (
        "account.move",
        "account_move",
        "move_type",
        "financial_type",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, field_renames)
