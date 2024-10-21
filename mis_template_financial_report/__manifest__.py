# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Profit & Loss / Balance sheet MIS templates",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "Hunki Enterprises BV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-reporting",
    "category": "Localization",
    "depends": ["mis_builder"],
    "data": [
        "data/mis_report_style.xml",
        "data/mis_report.xml",
        "data/mis_report_kpi.xml",
        "data/mis_report_subreport.xml",
        "views/mis_report_instance_views.xml",
        "views/mis_report_kpi_views.xml",
        "views/templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "mis_template_financial_report/static/src/components/mis_report_widget.xml",
            "mis_template_financial_report/static/src/components/mis_report_widget.css",
        ],
        "web.report_assets_common": [
            "mis_template_financial_report/static/src/css/report.css"
        ],
    },
    "maintainers": ["hbrunn"],
}
