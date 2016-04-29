# -*- coding: utf-8 -*-
# © 2016 Taktik
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account financial test data',
    'version': '9.0.1.0.0',
    'license': 'AGPL-3',
    'author': "Taktik, Odoo Community Association (OCA)",
    'category': 'Other',
    'depends': [
        "account_accountant",
        "l10n_fr",
    ],
    'demo': [],
    'data': [
        "data/settings_data.xml",
        "data/account_auto_installer.xml",
        "data/partners_data.xml",
        "data/products_data.xml",
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
}
