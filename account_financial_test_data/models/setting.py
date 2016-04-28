from openerp import api, models, fields, exceptions, _
from openerp.modules.module import get_module_resource


class SettingCurrency(models.Model):
    _name = 'setting.currency'

    @api.model
    def _update_currency(self):
        data_obj = self.env['ir.model.data']

        eur = data_obj.xmlid_to_object('base.EUR')
        usd = data_obj.xmlid_to_object('base.USD')

        eur.base = False
        self.env['res.currency.rate'].search([
            ('currency_id', '=', eur.id)
        ]).write({'rate': 0.8000})

        main_company = data_obj.xmlid_to_object('base.main_company')
        main_company.auto_currency_up = True

        services = self.env['currency.rate.update.service'].search(
            [('company_id', '=', main_company.id),
             ('service', '=', 'ECB_getter')]
        )
        if services:
            main_company.services_to_use = services[0]
        else:
            main_company.services_to_use = self.env[
                'currency.rate.update.service'
            ].create({
                    'service': 'ECB_getter',
                    'max_delta_days': 1,
                    'currency_to_update': [(6, 0, [eur.id, usd.id])]
            })

        main_company.button_refresh_currency()
