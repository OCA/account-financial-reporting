# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Analytic Cash Basis Report",
    "summary": "Cash-basis vs accrual analytic report, prorated by payment",
    "version": "16.0.1.0.0",
    "category": "Accounting/Reporting",
    "author": "PopSolutions, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-reporting",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "security/analytic_cash_basis_security.xml",
        "views/analytic_cash_basis_line_views.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["marcos-mendez"],
}
