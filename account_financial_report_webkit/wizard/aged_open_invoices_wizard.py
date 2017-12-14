# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Alexis de Lattre
#    Copyright 2015 Akretion (www.akretion.com)
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields


class AgedOpenInvoice(models.TransientModel):
    """Will launch age partner balance report.
    This report is based on Open Invoice Report
    and share a lot of knowledge with him
    """

    # pylint: disable=consider-merging-classes-inherited
    _inherit = "open.invoices.webkit"
    _name = "aged.open.invoices.webkit"
    _description = "Aged open invoices"

    filter = fields.Selection(default='filter_date')

    # pylint: disable=old-api7-method-defined
    def onchange_fiscalyear(self, cr, uid, ids, fiscalyear=False,
                            period_id=False, date_to=False, until_date=False,
                            context=None):
        res = super(AgedOpenInvoice, self).onchange_fiscalyear(
            cr, uid, ids, fiscalyear=fiscalyear, period_id=period_id,
            date_to=date_to, until_date=until_date, context=context
        )
        filters = self.onchange_filter(cr, uid, ids, filter='filter_period',
                                       fiscalyear_id=fiscalyear,
                                       context=context)
        res['value'].update({
            'period_from': filters['value']['period_from'],
            'period_to': filters['value']['period_to'],
        })
        return res

    # pylint: disable=old-api7-method-defined
    def _print_report(self, cr, uid, ids, data, context=None):
        # we update form with display account value
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.account_aged_open_invoices_webkit',
                'datas': data}
