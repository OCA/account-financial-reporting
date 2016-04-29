# -*- encoding: utf-8 -*-
##############################################################################
#
#    mis_builder module for Odoo, Management Information System Builder
#    Copyright (C) 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
#
#    This file is a part of mis_builder
#
#    mis_builder is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    mis_builder is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models, exceptions

class MisReportKpi(models.Model):

    _inherit='mis.report.kpi'

    @api.depends('kpi_style')
    def calc_css_style(self):
        css_attributes = [
            ('font-style', self.kpi_style.font_style),
            ('font-weight', self.kpi_style.font_weight),
            ('font-size',  self.kpi_style.font_size),
            ('color', self.kpi_style.color),
            ('background-color', self.kpi_style.background_color),
            ('indent-level', str(self.kpi_style.indent_level))
        ]

        css_list = [
            x[0] + ':' + x[1]  for x in css_attributes if x[1]
        ]
        self.default_css_style = ';'.join(css_item for css_item in css_list)


    # Adding Attributes to default_css_style
    default_css_style = fields.Char(compute=calc_css_style, store=True)
    kpi_style = fields.Many2one(
        string="Default CSS style for KPI",
        comodel_name="mis.report.kpi.style",
        required=True
    )


class MisReportKpiStyle(models.Model):

    _name = 'mis.report.kpi.style'

    # TODO use WEB WIdget color picker
    name = fields.Char(string='style name', required=True)


    @api.depends('indent_level')
    def check_positive_val(self):
        return self.indent_level > 0


    _font_style_selection = [
        ('normal', 'Normal'),
        ('italic', 'Italic'),
    ]

    _font_weight_selection = [
        ('nornal', 'Normal'),
        ('bold', 'Bold'),
    ]

    _font_size_selection = [
        ('medium', ''),
        ('xx-small', 'xx-small'),
        ('x-small', 'x-small'),
        ('small', 'small'),
        ('large', 'large'),
        ('x-large', 'x-large'),
        ('xx-large', 'xx-large'),
    ]


    color = fields.Char(
        required=True,
        help='Line color in valid RGB code (from #000000 to #FFFFFF)',
    )
    background_color = fields.Char(
        required=True,
        help='Line color in valid RGB code (from #000000 to #FFFFFF)'
    )
    font_style = fields.Selection(
        selection=_font_style_selection,
    )
    font_weight = fields.Selection(
        selection=_font_weight_selection
    )
    font_size = fields.Selection(
        selection=_font_size_selection
    )
    indent_level = fields.Integer()
