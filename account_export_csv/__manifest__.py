# Copyright 2013 Camptocamp SA
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Export CSV',
    'summary': "Adds accounting CSV export",
    'version': '12.0.1.2.0',
    'depends': [
        'account',
        'date_range',
    ],
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'website': 'http://www.camptocamp.com',
    'license': 'AGPL-3',
    'data': [
        'wizard/account_export_csv_view.xml',
    ],
    'installable': True,
}
