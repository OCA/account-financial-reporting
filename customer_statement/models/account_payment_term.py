# -*- coding: utf-8 -*-
# Copyright 2018 Graeme Gellatly
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountPaymentTerm(models.Model):

    _inherit = 'account.payment.term'

    aging_periods = fields.Integer(string='Aging Periods to show', default=4)

    @api.constrains('aging_periods')
    def _aging_period_limits(self):
        periods = self.mapped('aging_periods')
        if max(periods) > 5 or min(periods) < 0:
            raise ValidationError(_('Only between 0 and 5 Aging periods allowed'))
