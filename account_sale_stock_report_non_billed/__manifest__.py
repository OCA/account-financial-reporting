# Copyright 2022 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Account Sale Stock Report Non Billed",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-reporting",
    "depends": ["stock_picking_invoice_link"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/stock_move_non_billed_views.xml",
        "security/ir.model.access.csv",
        "wizard/account_sale_stock_report_non_billed_wiz_views.xml",
    ],
    "installable": True,
    "maintainers": ["CarlosRoca13"],
    "development_status": "Beta",
}
