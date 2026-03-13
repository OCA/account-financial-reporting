# Copyright 2026 PT Solusi Aglis Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
{
    "name": "Cash Basis Journal Items",
    "version": "14.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "PT Solusi Aglis Indonesia, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-reporting",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "views/cash_basis_move_line_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "maintainers": ["hitrosol"],
}
