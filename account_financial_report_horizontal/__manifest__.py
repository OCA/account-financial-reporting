# © 2012-2016 Therp BV <http://therp.nl>
# © 2013 Agile Business Group sagl <http://www.agilebg.com>
# <lorenzo.battistini@agilebg.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Accounting Financial Report Horizontal",
    "version": "11.0.1.0.0",
    "author": "Therp BV,Agile Business Group,Odoo Community Association (OCA)",
    "category": 'Accounting & Finance',
    'website': 'https://github.com/OCA/account-financial-reporting',
    'license': 'AGPL-3',
    "depends": ["account_invoicing"],
    'data': [
        "data/report_paperformat.xml",
        "data/ir_actions_report_xml.xml",
        "report/report_financial.xml",
    ],
}
