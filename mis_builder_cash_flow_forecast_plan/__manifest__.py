# © 2026 Solvos Consultoría Informática (<http://www.solvos.es>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    "name": "MIS Builder Cash Flow Forecast Plan",
    "version": "17.0.1.0.0",
    "summary": "Cash flow forecast line categories and recurrent cash flow plans.",
    "license": "AGPL-3",
    "author": "Solvos, " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-reporting",
    "depends": ["mis_builder_cash_flow"],
    "data": [
        "security/ir.model.access.csv",
        "security/mis_builder_cash_flow_extended_security.xml",
        "views/mis_cash_flow_category_views.xml",
        "views/mis_cash_flow_plan_views.xml",
        "views/mis_cash_flow_forecast_line_views.xml",
        "views/res_config_settings_views.xml",
        "data/mis_cash_flow_category.xml",
    ],
    "installable": True,
    "application": False,
}
