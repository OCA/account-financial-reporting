# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Partner Statement Periodic Mail Send",
    "summary": "Automatically send activity statements to customers monthly",
    "category": "Accounting & Finance",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-reporting",
    "depends": [
        "partner_statement",
    ],
    "data": [
        "data/mail_template.xml",
        "data/ir_cron.xml",
        "views/res_partner_views.xml",
    ],
}
