# -*- encoding: utf-8 -*-
##############################################################################
#
#    Report intrastat base module for OpenERP
#    Copyright (C) 2010-2013 Akretion (http://www.akretion.com/). All rights reserved.
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

from openerp.osv import osv
from openerp.tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

logger = logging.getLogger(__name__)


class report_intrastat_common(osv.TransientModel):
    _name = "report.intrastat.common"
    _description = "Common functions for intrastat reports for products and services"

    def _compute_numbers(self, cr, uid, ids, object, context=None):
        result = {}
        for intrastat in object.browse(cr, uid, ids, context=context):
            total_amount = 0.0
            num_lines = 0
            for line in intrastat.intrastat_line_ids:
                total_amount += line.amount_company_currency
                num_lines += 1
            result[intrastat.id] = {'num_lines': num_lines, 'total_amount': total_amount}
        return result


    def _compute_dates(self, cr, uid, ids, object, context=None):
        result = {}
        for intrastat in object.browse(cr, uid, ids, context=context):
            start_date_datetime = datetime.strptime(intrastat.start_date, '%Y-%m-%d')
            end_date_str = datetime.strftime(start_date_datetime + relativedelta(day=31), '%Y-%m-%d')
            result[intrastat.id] = {
                'end_date': end_date_str,
                'year_month': start_date_datetime.strftime('%Y-%m'),
                }
        return result


    def _check_start_date(self, cr, uid, ids, object, context=None):
        '''Check that the start date is the first day of the month'''
        for date_to_check in object.read(cr, uid, ids, ['start_date'], context=context):
            datetime_to_check = datetime.strptime(date_to_check['start_date'], '%Y-%m-%d')
            if datetime_to_check.day != 1:
                return False
        return True


    def _check_generate_lines(self, cr, uid, intrastat, context=None):
        if not intrastat.company_id.country_id:
            raise osv.except_osv(_('Error :'), _("The country is not set on the company '%s'.") %intrastat.company_id.name)
        if not intrastat.currency_id.name == 'EUR':
            raise osv.except_osv(_('Error :'), _("The company currency must be 'EUR', but is currently '%s'.") %intrastat.currency_id.name)
        return True


    def _check_generate_xml(self, cr, uid, intrastat, context=None):
        if not intrastat.company_id.partner_id.vat:
            raise osv.except_osv(_('Error :'), _("The VAT number is not set for the partner '%s'.") %intrastat.company_id.partner_id.name)
        return True


    def _check_xml_schema(self, cr, uid, xml_root, xml_string, xsd, context=None):
        '''Validate the XML file against the XSD'''
        from lxml import etree
        official_des_xml_schema = etree.XMLSchema(etree.fromstring(xsd))
        try: official_des_xml_schema.assertValid(xml_root)
        except Exception, e:   # if the validation of the XSD fails, we arrive here
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning("The XML file is invalid against the XML Schema Definition")
            _logger.warning(xml_string)
            _logger.warning(e)
            raise osv.except_osv(_('Error :'), _('The generated XML file is not valid against the official XML Schema Definition. The generated XML file and the full error have been written in the server logs. Here is the error, which may give you an idea on the cause of the problem : %s.') % str(e))
        return True


    def _attach_xml_file(self, cr, uid, ids, object, xml_string, start_date_datetime, declaration_name, context=None):
        '''Attach the XML file to the report_intrastat_product/service object'''
        import base64
        if len(ids) != 1:
            raise osv.except_osv(_('Error :'), 'Hara kiri in attach_xml_file')
        filename = datetime.strftime(start_date_datetime, '%Y-%m') + '_' + declaration_name + '.xml'
        attach_name = declaration_name.upper() + ' ' + datetime.strftime(start_date_datetime, '%Y-%m')
        attach_obj = self.pool.get('ir.attachment')
        if not context:
            context = {}
        context.update({'default_res_id' : ids[0], 'default_res_model': object._name})
        attach_id = attach_obj.create(cr, uid, {'name': attach_name, 'datas': base64.encodestring(xml_string), 'datas_fname': filename}, context=context)
        return attach_id


    def _open_attach_view(self, cr, uid, attach_id, title='XML file', context=None):
        '''Returns an action which opens the form view of the corresponding attachement'''
        # Only works in v6 -> not used in v5
        action = {
            'name': title,
            'view_type': 'form',
            'view_mode': 'form,tree',
            'view_id': False,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': attach_id,
            }
        return action


    def partner_on_change(self, cr, uid, ids, partner_id=False):
        result = {}
        result['value'] = {}
        if partner_id:
            company = self.pool.get('res.partner').read(cr, uid, partner_id, ['vat'])
            result['value'].update({'partner_vat': company['vat']})
        return result


    def send_reminder_email(self, cr, uid, company, module_name, template_xmlid, intrastat_id, context=None):
        template_data = self.pool['ir.model.data'].get_object_reference(cr, uid, module_name, template_xmlid)
        if template_data and template_data[0] == 'email.template':
            template_id = template_data[1]
        else:
            raise
        if company.intrastat_remind_user_ids:
            self.pool['email.template'].send_mail(cr, uid, template_id, intrastat_id, context=context)
            logger.info('Intrastat Reminder email has been sent (XMLID: %s).' % template_xmlid)
        else:
            logger.warning('The list of users receiving the Intrastat Reminder is empty on company %s' % company.name)
        return True
