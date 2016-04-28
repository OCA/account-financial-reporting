# -*- coding: utf-8 -*-
# © 2016 Therp BV SA/NV (<http://therp.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models, exceptions


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

    _font_size_to_size = {
        'medium': 11,
        'xx-small': 5,
        'x-small': 7,
        'small': 9,
        'large': 13,
        'x-large': 15,
        'xx-large': 17
    }

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

    @api.multi
    def font_size_to_size(self):
        self.ensure_one()
        return self._font_size_to_size.get(self.font_size, 11)

    @api.multi
    def to_xlsx_format_properties(self):
        self.ensure_one()
        props = {
            'italic': self.font_style == 'italic',
            'bold': self.font_weight == 'bold',
            'font_color': self.color,
            'bg_color': self.background_color,
            'indent': self.indent_level,
            'size': self.font_size_to_size()
        }
        return props

    @api.multi
    def to_css_style(self):
        self.ensure_one()
        css_attributes = [
            ('font-style', self.font_style),
            ('font-weight', self.font_weight),
            ('font-size',  self.font_size),
            ('color', self.color),
            ('background-color', self.background_color),
            ('indent-level', str(self.indent_level))
        ]

        css_list = [
            x[0] + ':' + x[1] for x in css_attributes if x[1]
        ]
        return ';'.join(css_item for css_item in css_list)
