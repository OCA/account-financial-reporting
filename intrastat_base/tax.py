# -*- encoding: utf-8 -*-
##############################################################################
#
#    Report intrastat base module for OpenERP
#    Copyright (C) 2011 Akretion (http://www.akretion.com). All Rights Reserved
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
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

from osv import osv, fields


class account_tax(osv.osv):
    _inherit = "account.tax"
    _columns = {
        'exclude_from_intrastat_if_present': fields.boolean('Exclude invoice line from intrastat if this tax is present', help="If this tax is present on an invoice line, this invoice line will be skipped when generating Intrastat Product or Service lines from invoices."),
    }

account_tax()

