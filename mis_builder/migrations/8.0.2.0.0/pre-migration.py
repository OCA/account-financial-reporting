# -*- coding: utf-8 -*-
# © 2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    cr.execute("""
        ALTER TABLE mis_report_kpi
        RENAME COLUMN expression TO old_expression
    """)
    # this migration to date_range type is partial,
    # actual date ranges needs to be created manually
    cr.execute("""
        UPDATE mis_report_instance_period
        SET type='date_range'
        WHERE type='fp'
    """)
