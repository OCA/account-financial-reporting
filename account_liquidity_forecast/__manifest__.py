# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
{
    "name": "Account Liquidity Forecast",
    "version": "16.0.1.0.0",
    "category": "Reporting",
    "summary": "Account Liquidity Forecast",
    "author": "ForgeFlow," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-reporting",
    "depends": ["account", "report_xlsx", "report_xlsx_helper"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "wizards/account_liquidity_forecast_wizard_views.xml",
        "views/report_liquidity_forecast_views.xml",
        "views/account_liquidity_forecast_planning_item_views.xml",
        "views/account_liquidity_forecast_planning_group_views.xml",
        "menuitems.xml",
        "reports.xml",
        "report/templates/layouts.xml",
        "report/templates/liquidity_forecast.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "account_liquidity_forecast/static/src/js/*",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "AGPL-3",
}
