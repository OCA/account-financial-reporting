# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
{
    "name": "Account Liquidity Forecast Purchase",
    "version": "16.0.1.0.0",
    "category": "Reporting",
    "summary": "Account Liquidity Forecast Purchase",
    "author": "ForgeFlow," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-reporting",
    "depends": ["account_liquidity_forecast", "purchase"],
    "data": [
        "wizards/account_liquidity_forecast_wizard_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "AGPL-3",
}
