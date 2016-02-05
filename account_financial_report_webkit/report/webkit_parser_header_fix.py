# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011 Camptocamp SA (http://www.camptocamp.com)
#
# Author: Guewen Baconnier (Camptocamp)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from mako.template import Template
from mako.lookup import TemplateLookup

import os
import subprocess
import tempfile
import logging
from functools import partial


from mako import exceptions
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from openerp import pooler
from openerp import tools
from openerp.addons.report_webkit import webkit_report
from openerp.addons.report_webkit.report_helper import WebKitHelper
from openerp.modules.module import get_module_resource

_logger = logging.getLogger('financial.reports.webkit')

# Class used only as a workaround to bug:
# http://code.google.com/p/wkhtmltopdf/issues/detail?id=656

# html headers and footers do not work on big files (hundreds of pages) so we
# replace them by text headers and footers passed as arguments to wkhtmltopdf
# this class has to be removed once the bug is fixed

# in your report class, to print headers and footers as text, you have to add
# them in the localcontext with a key 'additional_args'
# for instance:
#        header_report_name = _('PARTNER LEDGER')
#        footer_date_time = self.formatLang(str(datetime.today()),
#                                           date_time=True)
#        self.localcontext.update({
#            'additional_args': [
#                ('--header-font-name', 'Helvetica'),
#                ('--footer-font-name', 'Helvetica'),
#                ('--header-font-size', '10'),
#                ('--footer-font-size', '7'),
#                ('--header-left', header_report_name),
#                ('--footer-left', footer_date_time),
#                ('--footer-right', ' '.join((_('Page'), '[page]', _('of'),
#                                            '[topage]'))),
#                ('--footer-line',),
#            ],
#        })


# redefine mako_template as this is overriden by jinja since saas-1
# from openerp.addons.report_webkit.webkit_report import mako_template


def mako_template(text):
    """Build a Mako template.

    This template uses UTF-8 encoding
    """
    tmp_lookup = TemplateLookup(
    )  # we need it in order to allow inclusion and inheritance
    return Template(text, input_encoding='utf-8', output_encoding='utf-8',
                    lookup=tmp_lookup)


class HeaderFooterTextWebKitParser(webkit_report.WebKitParser):

    def generate_pdf(self, comm_path, report_xml, header, footer, html_list,
                     webkit_header=False, parser_instance=False):
        """Call webkit in order to generate pdf"""
        if not webkit_header:
            webkit_header = report_xml.webkit_header
        fd, out_filename = tempfile.mkstemp(suffix=".pdf",
                                            prefix="webkit.tmp.")
        file_to_del = [out_filename]
        if comm_path:
            command = [comm_path]
        else:
            command = ['wkhtmltopdf']

        command.append('--quiet')
        # default to UTF-8 encoding.  Use <meta charset="latin-1"> to override.
        command.extend(['--encoding', 'utf-8'])

        if webkit_header.margin_top:
            command.extend(
                ['--margin-top',
                 str(webkit_header.margin_top).replace(',', '.')])
        if webkit_header.margin_bottom:
            command.extend(
                ['--margin-bottom',
                 str(webkit_header.margin_bottom).replace(',', '.')])
        if webkit_header.margin_left:
            command.extend(
                ['--margin-left',
                 str(webkit_header.margin_left).replace(',', '.')])
        if webkit_header.margin_right:
            command.extend(
                ['--margin-right',
                 str(webkit_header.margin_right).replace(',', '.')])
        if webkit_header.orientation:
            command.extend(
                ['--orientation',
                 str(webkit_header.orientation).replace(',', '.')])
        if webkit_header.format:
            command.extend(
                ['--page-size',
                 str(webkit_header.format).replace(',', '.')])

        if parser_instance.localcontext.get('additional_args', False):
            for arg in parser_instance.localcontext['additional_args']:
                command.extend(arg)

        count = 0
        for html in html_list:
            with tempfile.NamedTemporaryFile(suffix="%d.body.html" % count,
                                             delete=False) as html_file:
                count += 1
                html_file.write(self._sanitize_html(html))
            file_to_del.append(html_file.name)
            command.append(html_file.name)
        command.append(out_filename)
        stderr_fd, stderr_path = tempfile.mkstemp(text=True)
        file_to_del.append(stderr_path)
        try:
            status = subprocess.call(command, stderr=stderr_fd)
            os.close(stderr_fd)  # ensure flush before reading
            stderr_fd = None  # avoid closing again in finally block
            fobj = open(stderr_path, 'r')
            error_message = fobj.read()
            fobj.close()
            if not error_message:
                error_message = _('No diagnosis message was provided')
            else:
                error_message = _(
                    'The following diagnosis message was provided:\n') + \
                    error_message
            if status:
                raise except_orm(_('Webkit error'),
                                 _("The command 'wkhtmltopdf' failed with \
                                 error code = %s. Message: %s") %
                                 (status, error_message))
            with open(out_filename, 'rb') as pdf_file:
                pdf = pdf_file.read()
            os.close(fd)
        finally:
            if stderr_fd is not None:
                os.close(stderr_fd)
            for f_to_del in file_to_del:
                try:
                    os.unlink(f_to_del)
                except (OSError, IOError), exc:
                    _logger.error('cannot remove file %s: %s', f_to_del, exc)
        return pdf

    # override needed to keep the attachments' storing procedure
    def create_single_pdf(self, cursor, uid, ids, data, report_xml,
                          context=None):
        """generate the PDF"""

        if context is None:
            context = {}
        htmls = []
        if report_xml.report_type != 'webkit':
            return super(HeaderFooterTextWebKitParser, self
                         ).create_single_pdf(cursor, uid, ids, data,
                                             report_xml, context=context)

        parser_instance = self.parser(cursor,
                                      uid,
                                      self.name2,
                                      context=context)

        self.pool = pooler.get_pool(cursor.dbname)
        objs = self.getObjects(cursor, uid, ids, context)
        parser_instance.set_context(objs, data, ids, report_xml.report_type)

        template = False

        if report_xml.report_file:
            path = get_module_resource(
                *report_xml.report_file.split(os.path.sep))
            if os.path.exists(path):
                template = file(path).read()
        if not template and report_xml.report_webkit_data:
            template = report_xml.report_webkit_data
        if not template:
            raise except_orm(
                _('Error!'), _('Webkit Report template not found !'))
        header = report_xml.webkit_header.html

        if not header and report_xml.header:
            raise except_orm(
                _('No header defined for this Webkit report!'),
                _('Please set a header in company settings.')
            )

        css = report_xml.webkit_header.css
        if not css:
            css = ''

        translate_call = partial(self.translate_call, parser_instance)
        # default_filters=['unicode', 'entity'] can be used to set global
        # filter
        body_mako_tpl = mako_template(template)
        helper = WebKitHelper(cursor, uid, report_xml.id, context)
        if report_xml.precise_mode:
            for obj in objs:
                parser_instance.localcontext['objects'] = [obj]
                try:
                    html = body_mako_tpl.render(helper=helper,
                                                css=css,
                                                _=translate_call,
                                                **parser_instance.localcontext)
                    htmls.append(html)
                except Exception:
                    msg = exceptions.text_error_template().render()
                    _logger.error(msg)
                    raise except_orm(_('Webkit render'), msg)
        else:
            try:
                html = body_mako_tpl.render(helper=helper,
                                            css=css,
                                            _=translate_call,
                                            **parser_instance.localcontext)
                htmls.append(html)
            except Exception:
                msg = exceptions.text_error_template().render()
                _logger.error(msg)
                raise except_orm(_('Webkit render'), msg)

        # NO html footer and header because we write them as text with
        # wkhtmltopdf
        head = foot = False

        if report_xml.webkit_debug:
            try:
                deb = body_mako_tpl.render(helper=helper,
                                           css=css,
                                           _debug=tools.ustr("\n".join(htmls)),
                                           _=translate_call,
                                           **parser_instance.localcontext)
            except Exception:
                msg = exceptions.text_error_template().render()
                _logger.error(msg)
                raise except_orm(_('Webkit render'), msg)
            return (deb, 'html')
        bin = self.get_lib(cursor, uid)
        pdf = self.generate_pdf(bin, report_xml, head, foot, htmls,
                                parser_instance=parser_instance)
        return (pdf, 'pdf')
