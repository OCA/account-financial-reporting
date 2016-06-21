# -*- coding: utf-8 -*-
##############################################################################
#
#    Intrastat base module for Odoo
#    Copyright (C) 2013-2014 Akretion (http://www.akretion.com)
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

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    intrastat_remind_user_ids = fields.Many2many(
        'res.users', column1='company_id', column2='user_id',
        string="Users Receiving the Intrastat Reminder",
        help="List of OpenERP users who will receive a notification to "
        "remind them about the Intrastat declaration.")
    intrastat_email_list = fields.Char(
        compute='_compute_intrastat_email_list',
        string='List of emails of Users Receiving the Intrastat Reminder')

    @api.multi
    @api.depends(
        'intrastat_remind_user_ids', 'intrastat_remind_user_ids.email')
    def _compute_intrastat_email_list(self):
        for this in self:
            emails = []
            for user in this.intrastat_remind_user_ids:
                if user.email:
                    emails.append(user.email)
            this.intrastat_email_list = ','.join(emails)

    @api.multi
    @api.constrains('intrastat_remind_user_ids')
    def _check_intrastat_remind_users(self):
        for this in self:
            for user in this.intrastat_remind_user_ids:
                if not user.email:
                    raise ValidationError(
                        _("Missing e-mail address on user '%s'.") %
                        (user.name))
