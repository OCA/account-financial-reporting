# -*- coding: utf-8 -*-
# © 2018 Sunflower IT (http://sunflowerweb.nl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.multi
    def print_debtor_card(self):
        """Button to print the sale orders and related invoices"""
        return self.env['report'].get_action(
            self, 'account_debtor_card.report_debtor_card')
