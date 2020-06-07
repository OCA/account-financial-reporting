# Copyright 2017-2020 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Bank Reconciliation Report",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-reporting",
    "summary": "XLSX report to help on bank reconciliation",
    "depends": ["account_financial_report", "report_xlsx"],
    "data": [
        "report/report.xml",
        "wizard/bank_reconciliation_report_wizard_view.xml",
        "views/account_bank_statement.xml",
        "views/account_move_line.xml",
        "views/account_journal.xml",
    ],
    "installable": True,
}
