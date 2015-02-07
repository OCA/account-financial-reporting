# -*- encoding: utf-8 -*-
##############################################################################
#
#    Report intrastat base module for Odoo
#    Copyright (C) 2010-2014 Akretion (http://www.akretion.com/).
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

from openerp import models, fields, api, tools, _
from openerp.exceptions import Warning, ValidationError
from dateutil.relativedelta import relativedelta
import logging

logger = logging.getLogger(__name__)


class ReportIntrastatCommon(models.AbstractModel):
    _name = "report.intrastat.common"
    _description = "Common functions for intrastat reports for products "
    "and services"

    @api.one
    @api.depends(
        'intrastat_line_ids', 'intrastat_line_ids.amount_company_currency')
    def _compute_numbers(self):
        total_amount = 0.0
        num_lines = 0
        for line in self.intrastat_line_ids:
            total_amount += line.amount_company_currency
            num_lines += 1
        self.num_lines = num_lines
        self.total_amount = total_amount

    @api.one
    @api.depends('start_date')
    def _compute_dates(self):
        start_date_dt = fields.Date.from_string(self.start_date)
        self.end_date = fields.Date.to_string(
            start_date_dt + relativedelta(day=31))
        self.year_month = start_date_dt.strftime('%Y-%m')

    @api.one
    def _check_start_date(self):
        '''Check that the start date is the first day of the month'''
        datetime_to_check = fields.Date.from_string(self.start_date)
        if datetime_to_check.day != 1:
            raise ValidationError(
                _('The start date must be the first day of the month'))

    @api.one
    def _check_generate_lines(self):
        if not self.company_id.country_id:
            raise Warning(
                _("The country is not set on the company '%s'.")
                % self.company_id.name)
        if self.currency_id.name != 'EUR':
            raise Warning(
                _("The company currency must be 'EUR', but is currently '%s'.")
                % self.currency_id.name)
        return True

    @api.one
    def _check_generate_xml(self):
        if not self.company_id.partner_id.vat:
            raise Warning(
                _("The VAT number is not set for the partner '%s'.")
                % self.company_id.partner_id.name)
        return True

    @api.model
    def _check_xml_schema(self, xml_root, xml_string, xsd_file):
        '''Validate the XML file against the XSD'''
        from lxml import etree
        xsd_etree_obj = etree.parse(
            tools.file_open(xsd_file))
        official_schema = etree.XMLSchema(xsd_etree_obj)
        try:
            official_schema.assertValid(xml_root)
        except Exception, e:
            # if the validation of the XSD fails, we arrive here
            logger = logging.getLogger(__name__)
            logger.warning(
                "The XML file is invalid against the XML Schema Definition")
            logger.warning(xml_string)
            logger.warning(e)
            raise Warning(
                _("The generated XML file is not valid against the official "
                    "XML Schema Definition. The generated XML file and the "
                    "full error have been written in the server logs. "
                    "Here is the error, which may give you an idea on the "
                    "cause of the problem : %s.")
                % str(e))
        return True

    @api.multi
    def _attach_xml_file(self, xml_string, declaration_name):
        '''Attach the XML file to the report_intrastat_product/service '''
        '''object'''
        self.ensure_one()
        import base64
        filename = '%s_%s.xml' % (self.year_month, declaration_name)
        attach = self.with_context(
            default_res_id=self.id,
            default_res_model=self._name).env['ir.attachment'].create({
            'name': filename,
            'datas': base64.encodestring(xml_string),
            'datas_fname': filename})
        return attach.id

    @api.model
    def _open_attach_view(self, attach_id, title='XML file'):
        '''Returns an action which opens the form view of the '''
        '''corresponding attachement'''
        action = {
            'name': title,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': attach_id,
            }
        return action

    @api.one
    def send_reminder_email(self, mail_template_xmlid):
        mail_template = self.env.ref(mail_template_xmlid)
        if self.company_id.intrastat_remind_user_ids:
            self.pool['email.template'].send_mail(
                self._cr, self._uid, mail_template.id, self.id,
                context=self._context)
            logger.info(
                'Intrastat Reminder email has been sent (XMLID: %s).'
                % mail_template_xmlid)
        else:
            logger.warning(
                'The list of users receiving the Intrastat Reminder is empty '
                'on company %s' % self.company_id.name)
        return True

    @api.multi
    def unlink(self):
        for intrastat in self:
            if intrastat.state == 'done':
                raise Warning(
                    _('Cannot delete the declaration %s '
                        'because it is in Done state') % self.year_month)
        return super(ReportIntrastatCommon, self).unlink()
