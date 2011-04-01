# -*- encoding: utf-8 -*-
##############################################################################
#
#    Report intrastat module for OpenERP
#    Copyright (C) 2010-2011 Akretion (http://www.akretion.com/). All rights reserved.
#       Code written by Alexis de Lattre <alexis.delattre@akretion.com>
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
import netsvc
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from tools.translate import _

class report_intrastat_common(osv.osv_memory):
    _name = "report.intrastat.common"
    _description = "Common functions for intrastat reports for products and services"

    def _compute_numbers(self, cr, uid, ids, object, context=None):
        print "COMMON START compute numbers ids=", ids
        result = {}
        for intrastat in object.browse(cr, uid, ids, context=context):
            total_amount = 0.0
            num_lines = 0
            for line in intrastat.intrastat_line_ids:
                total_amount += line.amount_company_currency
                num_lines += 1
            result[intrastat.id] = {'num_lines': num_lines, 'total_amount': total_amount}
        print "COMMON _compute_numbers res = ", result
        return result


    def _compute_end_date(self, cr, uid, ids, object, context=None):
        print "COMMON _compute_end_date START ids=", ids
        result = {}
        for intrastat in object.browse(cr, uid, ids, context=context):
            start_date_datetime = datetime.strptime(intrastat.start_date, '%Y-%m-%d')
            end_date_str = datetime.strftime(start_date_datetime + relativedelta(day=31), '%Y-%m-%d')
            result[intrastat.id] = end_date_str
        print "COMMON _compute_end_date res=", result
        return result


    def _check_start_date(self, cr, uid, ids, object, context=None):
        '''Check that the start date if the first day of the month'''
        for date_to_check in object.read(cr, uid, ids, ['start_date'], context=context):
            datetime_to_check = datetime.strptime(date_to_check['start_date'], '%Y-%m-%d')
            if datetime_to_check.day != 1:
                return False
        return True

    def generate_service_lines(self, cr, uid, ids, context=None):
        print "generate lines, ids=", ids
        if len(ids) != 1:
            raise osv.except_osv(_('Error :'), _('Hara kiri in generate_service_lines'))
        intrastat = self.browse(cr, uid, ids[0], context=context)
        # Check that the company currency is EUR
        if not intrastat.currency_id.code == 'EUR':
            raise osv.except_osv(_('Error :'), _('The company currency must be "EUR", but is currently "%s".'%intrastat.currency_id.code))
        # Get current service lines and delete them
        line_remove = self.read(cr, uid, ids[0], ['intrastat_line_ids'], context=context)
        print "line_remove", line_remove
        if line_remove['intrastat_line_ids']:
            self.pool.get('report.intrastat.service.line').unlink(cr, uid, line_remove['intrastat_line_ids'], context=context)
        sql = '''
        select
            min(inv_line.id) as id,
            company.id,
            inv.name as name,
            inv.number as invoice_number,
            inv.date_invoice,
            inv.currency_id as invoice_currency_id,
            prt.vat as partner_vat,
            prt.name as partner_name,
            res_currency_rate.rate as invoice_currency_rate,
            sum(case when inv.type = 'out_refund'
                then inv_line.price_subtotal * (-1)
                when inv.type = 'out_invoice'
                then inv_line.price_subtotal
               end) as amount_invoice_currency,
            sum(case when company.currency_id != inv.currency_id and res_currency_rate.rate is not null
                then
                  case when inv.type = 'out_refund'
                    then round(inv_line.price_subtotal/res_currency_rate.rate * (-1), 2)
                  when inv.type = 'out_invoice'
                    then round(inv_line.price_subtotal/res_currency_rate.rate, 2)
                  end
                when company.currency_id = inv.currency_id
                then
                   case when inv.type = 'out_refund'
                     then inv_line.price_subtotal * (-1)
                   when inv.type = 'out_invoice'
                     then inv_line.price_subtotal
                   end
                end) as amount_company_currency,
                company.currency_id as company_currency_id

        from account_invoice inv
            left join account_invoice_line inv_line on inv_line.invoice_id=inv.id
            left join (product_template pt
                left join product_product pp on pp.product_tmpl_id = pt.id
                )
            on (inv_line.product_id = pt.id)
            left join (res_partner_address inv_address
                left join res_country inv_country on (inv_country.id = inv_address.country_id))
            on (inv_address.id = inv.address_invoice_id)
            left join res_partner prt on inv.partner_id = prt.id
            left join report_intrastat_type intr on inv.intrastat_type_id = intr.id
            left join res_currency_rate on (inv.currency_id = res_currency_rate.currency_id and inv.date_invoice = res_currency_rate.name)
            left join res_company company on inv.company_id=company.id

        where
            inv.type in ('out_invoice', 'out_refund')
            and inv.state in ('open', 'paid')
            and inv_line.product_id is not null
            and inv_line.price_subtotal != 0
            and inv_country.intrastat = true
            and pt.type = 'service'
            and pt.exclude_from_intrastat is not true
            and intr.type != 'other'
            and company.id = %s
            and inv.date_invoice >= %s
            and inv.date_invoice <= %s

        group by company.id, inv.date_invoice, inv.number, inv.currency_id, prt.vat, prt.name, inv.name, invoice_currency_rate, company_currency_id
        '''
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company_id = str(user.company_id.id)
        print "company_id =", company_id
        start_date_str = intrastat.start_date
        end_date_str = intrastat.end_date
        # Execute the big SQL query to get all service lines
        cr.execute(sql, (company_id, start_date_str, end_date_str))
        res_sql = cr.fetchall()
        print "res_sql=", res_sql
        line_obj = self.pool.get('report.intrastat.service.line')
        for id, name, company_id, invoice_number, date_invoice, invoice_currency_id, partner_vat, partner_name, invoice_currency_rate, amount_invoice_currency, amount_company_currency, company_currency_id in res_sql:
            print "amount_invoice_currency =", amount_invoice_currency
            print "amount_company_currency =", amount_company_currency
            # Store the service lines
            line_obj.create(cr, uid, {
                'parent_id': ids[0],
                'name': name,
                'invoice_number': invoice_number,
                'partner_vat': partner_vat,
                'partner_name': partner_name,
                'date_invoice': date_invoice,
                'amount_invoice_currency': int(round(amount_invoice_currency, 0)),
                'invoice_currency_id': invoice_currency_id,
                'amount_company_currency': int(round(amount_company_currency, 0)),
                'company_currency_id': company_currency_id,
                    }, context=context)
        return None


    def done(self, cr, uid, ids, context=None):
        if len(ids) != 1:
            raise osv.except_osv(_('Error :'), _('Hara kiri in generate_xml'))
        self.write(cr, uid, ids[0], {'state': 'done'}, context=context)
        return None

    def back2draft(self, cr, uid, ids, context=None):
        if len(ids) != 1:
            raise osv.except_osv(_('Error :'), _('Hara kiri in generate_xml'))
        self.write(cr, uid, ids[0], {'state': 'draft'}, context=context)
        return None


    def generate_xml(self, cr, uid, ids, context=None):
        intrastat = self.browse(cr, uid, ids[0], context=context)
        start_date_str = intrastat.start_date
        end_date_str = intrastat.end_date
        start_date_datetime = datetime.strptime(start_date_str, '%Y-%m-%d')

        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)

        if not intrastat.currency_id.code == 'EUR':
            raise osv.except_osv(_('Error :'), _('The company currency must be "EUR", but is currently "%s".'%intrastat.currency_id.code))

        if not user.company_id.partner_id.vat:
            raise osv.except_osv(_('Error :'), _('The VAT number is not set for the partner "%s".'%user.company_id.partner_id.name))
        my_company_vat = user.company_id.partner_id.vat.replace(' ', '')

        # Tech spec of XML export are available here :
        # https://pro.douane.gouv.fr/download/downloadUrl.asp?file=PubliwebBO/fichiers/DES_DTIPlus.pdf
        root = etree.Element('fichier_des')
        decl = etree.SubElement(root, 'declaration_des')
        num_des = etree.SubElement(decl, 'num_des')
        num_des.text = datetime.strftime(start_date_datetime, '%Y%m')
        num_tva = etree.SubElement(decl, 'num_tvaFr')
        num_tva.text = my_company_vat
        mois_des = etree.SubElement(decl, 'mois_des')
        mois_des.text = datetime.strftime(start_date_datetime, '%m') # month 2 digits
        an_des = etree.SubElement(decl, 'an_des')
        an_des.text = datetime.strftime(start_date_datetime, '%Y')
        line = 0
        # we now go through each service line
        for sline in intrastat.intrastat_line_ids:
            line += 1 # increment line number
            ligne_des = etree.SubElement(decl, 'ligne_des')
            numlin_des = etree.SubElement(ligne_des, 'numlin_des')
            numlin_des.text = str(line)
            valeur = etree.SubElement(ligne_des, 'valeur')
            # We take amount_company_currency, to be sure we have amounts in EUR
            valeur.text = str(sline.amount_company_currency)
            partner_des = etree.SubElement(ligne_des, 'partner_des')
            try: partner_des.text = sline.partner_vat.replace(' ', '')
            except: raise osv.except_osv(_('Error :'), _('Missing VAT number for partner "%s".'%sline.partner_name))
        xml_string = etree.tostring(root, pretty_print=True, encoding='UTF-8', xml_declaration=True)
        print "xml_string", xml_string

        # We now validate the XML file against the official XML Schema Definition
        official_des_xml_schema = etree.XMLSchema(etree.fromstring(des_xsd.des_xsd))
        try: official_des_xml_schema.assertValid(root)
        except Exception, e:   # if the validation of the XSD fails, we arrive here
            logger = netsvc.Logger()
            logger.notifyChannel('intrastat_service', netsvc.LOG_WARNING, "The XML file is invalid against the XSD")
            logger.notifyChannel('intrastat_service', netsvc.LOG_WARNING, xml_string)
            logger.notifyChannel('intrastat_service', netsvc.LOG_WARNING, e)
            raise osv.except_osv(_('Error :'), _('The generated XML file is not valid against the official XML schema. The generated XML file and the full error have been written in the server logs. Here is the exact error, which may give you an idea of the cause of the problem : ' + str(e)))
        #let's give a pretty name to the filename : <year-month_des.xml>
        filename = datetime.strftime(start_date_datetime, '%Y-%m') + '_des.xml'
        attach_name = 'DES ' + datetime.strftime(start_date_datetime, '%Y-%m')

        # Attach the XML file to the intrastat_service object
        attach_obj = self.pool.get('ir.attachment')
        if not context:
            context = {}
        context.update({'default_res_id' : ids[0], 'default_res_model': 'report.intrastat.service'})
        attach_id = attach_obj.create(cr, uid, {'name': attach_name, 'datas': base64.encodestring(xml_string), 'datas_fname': filename}, context=context)
        return None


report_intrastat_common()

