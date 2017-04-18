# -*- coding: utf-8 -*-
# Copyright 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
# Copyright 2015 Tecnativa - Pedro M. Baeza
# Copyright 2017 RGB Consulting
# Copyright 2017 Eficent - Miquel Raich
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Journal Report",
    'version': "9.0.1.0.0",
    'depends': [
        "account",
        "report_xlsx",
    ],
    'license': "AGPL-3",
    'author': "J. Gutierrez, "
              "Tecnativa, "
              "RGB Consulting, "
              "Eficent, "
              "Odoo Community Association (OCA)",
    'website': "http://github.com/OCA/account-financial-reporting",
    'category': "Accounting",
    'summary': "Journal Report",
    'data': [
        "wizard/wizard_print_journal_ledger_view.xml",
        "report/reports.xml",
        "views/templates.xml",
    ],
    "installable": True,
}
