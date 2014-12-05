# -*- encoding: utf-8 -*-
##############################################################################
#
#    Authors: Matthieu Dietrich
#    Copyright Camptocamp SA 2014
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
import os
import logging
import tempfile
import zipfile
from functools import partial

from mako import exceptions
from openerp.osv.osv import except_osv
from openerp.tools.translate import _
from openerp import addons
from openerp import pooler
from openerp.addons.account_financial_report_webkit.report.\
    webkit_parser_header_fix import HeaderFooterTextWebKitParser
from openerp.addons.report_webkit.report_helper import WebKitHelper
from .ledger_balance import LedgerBalanceWebkit

_logger = logging.getLogger('financial.reports.webkit')

# redefine mako_template as this is overriden by jinja since saas-1
# from openerp.addons.report_webkit.webkit_report import mako_template
from mako.template import Template
from mako.lookup import TemplateLookup


def mako_template(text):
    """Build a Mako template.

    This template uses UTF-8 encoding
    """
    tmp_lookup = TemplateLookup()  # we need it in order to allow inclusion
    return Template(text, input_encoding='utf-8',
                    output_encoding='utf-8', lookup=tmp_lookup)


class MultipleFilesWebKitParser(HeaderFooterTextWebKitParser):

    def create(self, cr, uid, ids, data, context=None):
        self.pool = pooler.get_pool(cr.dbname)
        self.cr = cr
        self.uid = uid
        report_obj = self.pool.get('ir.actions.report.xml')
        report_ids = report_obj.search(cr, uid,
                                       [('report_name', '=', self.name[7:])],
                                       context=context)
        if report_ids:
            report_xml = report_obj.browse(
                cr, uid, report_ids[0], context=context
            )
            self.title = report_xml.name
            if report_xml.report_type == 'zip':
                return self.create_zip_report(
                    cr, uid, ids, data, report_xml, context
                )
        return super(MultipleFilesWebKitParser, self).create(
            cr, uid, ids, data, context
        )

    # Use this method to write multiple PDF files in one ZIP file.
    def create_zip_report(self, cursor, uid, ids, data,
                          report_xml, context=None):

        if context is None:
            context = {}
        bin = self.get_lib(cursor, uid)

        # NO html footer and header because we write them as text with
        # wkhtmltopdf
        head = foot = False
        css = report_xml.webkit_header.css
        if not css:
            css = ''

        # Parser instance for accounts
        parser_instance = self.parser(cursor,
                                      uid,
                                      self.name2,
                                      context=context)
        template = False
        if report_xml.report_file:
            path = addons.get_module_resource(
                *report_xml.report_file.split(os.path.sep)
            )
            if os.path.exists(path):
                template = file(path).read()
        if not template and report_xml.report_webkit_data:
            template = report_xml.report_webkit_data
        if not template:
            raise except_osv(_('Error!'),
                             _('Webkit Report template not found !'))
        translate_call = partial(self.translate_call, parser_instance)
        body_mako_tpl = mako_template(template)
        helper = WebKitHelper(cursor, uid, report_xml.id, context)

        # Parser for the balance
        report_obj = self.pool.get('ir.actions.report.xml')
        balance_report_ids = report_obj.search(
            cursor, uid,
            [('report_name',
              '=',
              'account.account_report_ledger_balance_webkit')],
            context=context
        )
        balance_report = report_obj.browse(
            cursor, uid, balance_report_ids[0], context=context
        )
        balance_template = False
        if balance_report.report_file:
            path = addons.get_module_resource(
                *balance_report.report_file.split(os.path.sep)
            )
            if os.path.exists(path):
                balance_template = file(path).read()
        if not balance_template and balance_report.report_webkit_data:
            balance_template = balance_report.report_webkit_data
        if not balance_template:
            raise except_osv(_('Error!'),
                             _('Webkit Report template not found !'))
        balance_mako_tpl = mako_template(balance_template)

        # create zip file
        try:
            fd, out_filename = tempfile.mkstemp(suffix=".zip",
                                                prefix="webkit.tmp.")
            zf = zipfile.ZipFile(out_filename, 'w')

            # create list to store cumulated balances
            cumulated_balances = []
            # Retrieve all accounts to process them separately
            account_ids = parser_instance.get_account_ids(
                cursor, uid, ids, data, context=context
            )
            for account_id in account_ids:
                parser_instance.set_context(
                    [], data, [account_id], report_xml.report_type
                )
                # Store cumulated balance for account
                if 'cumulated_balance' in parser_instance.localcontext:
                    cumulated_balances.append(
                        parser_instance.localcontext['cumulated_balance']
                    )

                objects = parser_instance.localcontext['objects']
                for object in objects:
                    # Pass one object at the time
                    parser_instance.localcontext['objects'] = [object]
                    try:
                        html = body_mako_tpl.render(
                            helper=helper, css=css, _=translate_call,
                            **parser_instance.localcontext
                        )
                        pdf = self.generate_pdf(
                            bin, report_xml, head, foot, [html],
                            parser_instance=parser_instance
                        )
                        if not object.file_name:
                            raise except_osv(
                                _('File name'),
                                _('The file name was not specified!')
                            )
                        zf.writestr(object.file_name, pdf)
                    except Exception:
                        msg = exceptions.text_error_template().render()
                        _logger.error(msg)
                        raise except_osv(_('Webkit render'), msg)

            # Print balance file and add to root
            balance_parser_instance = LedgerBalanceWebkit(
                cursor, uid,
                'report.account.account_report_ledger_balance_webkit',
                context=context
            )
            balance_parser_instance.set_context(
                cumulated_balances, data, [], balance_report.report_type
            )
            try:
                balance_html = balance_mako_tpl.render(
                    helper=helper, css=css, _=translate_call,
                    **balance_parser_instance.localcontext
                )
                balance_pdf = self.generate_pdf(
                    bin, balance_report, head, foot, [balance_html],
                    parser_instance=balance_parser_instance
                )
                zf.writestr("0 - " +
                            _('Cumulated Balance on Accounts') +
                            ".pdf",
                            balance_pdf)
            except Exception:
                msg = exceptions.text_error_template().render()
                _logger.error(msg)
                raise except_osv(_('Webkit render'), msg)

            # Close Zip file
            zf.close()
            with open(out_filename, 'rb') as zip_file:
                zip = zip_file.read()
            os.close(fd)
        finally:
            try:
                os.unlink(out_filename)
            except (OSError, IOError), exc:
                _logger.error('cannot remove ZIP file %s: %s',
                              out_filename, exc)

        return (zip, 'zip')
