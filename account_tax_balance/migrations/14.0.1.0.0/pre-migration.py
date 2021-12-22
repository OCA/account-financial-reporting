# Copyright 2020 Ozono Multimedia S.L.L.
# Copyright 2021 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """
    Column `move_type` of table `account_move` has been renamed to `financial_type`
    because `move_type` is now used by the core,
    so the column is moved during migration of module `account` in the core.
    Enterprise renames it to `move_type_custom`;
    OpenUpgrade renames it to its legacy name.
    Move data from the renamed column to the new `financial_type` column.
    """
    old_move_type_column = "move_type"
    new_move_type_column = "financial_type"
    move_model_name = "account.move"
    move_table_name = "account_move"
    enterprise_move_type_rename = "move_type_custom"
    ou_move_type_rename = openupgrade.get_legacy_name(old_move_type_column)

    for move_type_rename in (enterprise_move_type_rename, ou_move_type_rename):
        if openupgrade.column_exists(env.cr, move_table_name, move_type_rename):
            openupgrade.rename_fields(
                env,
                [
                    (
                        move_model_name,
                        move_table_name,
                        move_type_rename,
                        new_move_type_column,
                    ),
                ],
            )
            break
