# -*- encoding: utf-8 -*-
##############################################################################
#
#    Intrastat base module for OpenERP
#    Copyright (C) 2013 Akretion (http://www.akretion.com)
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

from openerp.osv import orm, fields
from openerp.tools.translate import _


class res_company(orm.Model):
    _inherit = "res.company"

    def _compute_intrastat_email_list(
            self, cr, uid, ids, name, arg, context=None):
        result = {}
        for company in self.browse(cr, uid, ids, context=context):
            result[company.id] = ''
            for user in company.intrastat_remind_user_ids:
                if result[company.id]:
                    result[company.id] += ',%s' % (user.email)
                else:
                    result[company.id] = user.email
        return result

    _columns = {
        'intrastat_remind_user_ids': fields.many2many(
            'res.users', id1='company_id', id2='user_id',
            string="Users Receiving the Intrastat Reminder",
            help="List of OpenERP users who will receive a notification to "
            "remind them about the Intrastat declaration."),
        'intrastat_email_list': fields.function(
            _compute_intrastat_email_list, type='char', size=1000,
            string='List of emails of Users Receiving the Intrastat Reminder'),
    }

    def _check_intrastat_remind_users(self, cr, uid, ids):
        for company in self.browse(cr, uid, ids):
            for user in company.intrastat_remind_user_ids:
                if not user.email:
                    raise orm.except_orm(
                        _('Error :'),
                        _("Missing e-mail address on user '%s'.")
                        % (user.name))
        return True

    _constraints = [
        (_check_intrastat_remind_users, "error msg in raise",
            ['intrastat_remind_user_ids']),
    ]
