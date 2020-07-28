# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Dutch MIS Builder templates",
    "summary": "Profit & Loss / Balance sheet for the Netherlands",
    "version": "12.0.1.1.0",
    "license": "AGPL-3",
    "author": "Hunki Enterprises BV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-netherlands",
    'category': "Localization",
    "depends": ["mis_builder"],
    "data": [
        "data/mis_report_style.xml",
        "data/mis_report.xml",
        "data/mis_report_kpi.xml",
        "data/mis_report_subreport.xml",
        "views/templates.xml",
    ],
    "qweb": ["static/src/xml/l10n_nl_mis_reports.xml"],
    "maintainers": ["hbrunn"],
}
