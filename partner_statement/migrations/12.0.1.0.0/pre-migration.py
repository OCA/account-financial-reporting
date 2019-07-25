# Copyright 2019 Eficent <http://www.eficent.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def rename_wizards(cr):
    if openupgrade.table_exists(cr, 'customer_activity_statement_wizard'):
        openupgrade.rename_tables(cr, [(
            'customer_activity_statement_wizard',
            'activity_statement_wizard'),
        ])
        openupgrade.rename_models(cr, [(
            'customer.activity.statement.wizard',
            'activity.statement.wizard'),
        ])
    if openupgrade.table_exists(cr, 'customer_outstanding_statement_wizard'):
        openupgrade.rename_tables(cr, [(
            'customer_outstanding_statement_wizard',
            'outstanding_statement_wizard'),
        ])
        openupgrade.rename_models(cr, [(
            'customer.outstanding.statement.wizard',
            'outstanding.statement.wizard'),
        ])


@openupgrade.migrate()
def migrate(env, version):
    rename_wizards(env.cr)
