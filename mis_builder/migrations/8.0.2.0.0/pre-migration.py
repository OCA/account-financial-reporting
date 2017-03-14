# -*- coding: utf-8 -*-
# © 2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    cr.execute("""
        ALTER TABLE mis_report_kpi
        RENAME COLUMN expression TO old_expression
    """)
