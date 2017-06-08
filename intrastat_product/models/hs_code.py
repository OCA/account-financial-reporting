# -*- coding: utf-8 -*-
##############################################################################
#
#    Intrastat Product module for Odoo
#    Copyright (C) 2011-2015 Akretion (http://www.akretion.com)
#    Copyright (C) 2009-2015 Noviat (http://www.noviat.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Luc de Meyer <info@noviat.com>
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

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class HSCode(models.Model):
    _inherit = "hs.code"

    intrastat_unit_id = fields.Many2one(
        'intrastat.unit', string='Intrastat Supplementary Unit')

    @api.constrains('local_code')
    def _hs_code(self):
        if self.company_id.country_id.intrastat:
            if not self.local_code.isdigit():
                raise ValidationError(
                    _("Intrastat Codes should only contain digits. "
                      "This is not the case for code '%s'.")
                    % self.local_code)
            if len(self.local_code) != 8:
                raise ValidationError(
                    _("Intrastat Codes should "
                      "contain 8 digits. This is not the case for "
                      "Intrastat Code '%s' which has %d digits.")
                    % (self.local_code, len(self.local_code)))
