# -*- coding: utf-8 -*-
# © 2014-2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models, _

import datetime
import logging

from .aep import AccountingExpressionProcessor as AEP

_logger = logging.getLogger(__name__)


class MisReportInstancePeriod(models.Model):
    """ A MIS report instance has the logic to compute
    a report template for a given date period.

    Periods have a duration (day, week, fiscal period) and
    are defined as an offset relative to a pivot date.
    """

    @api.one
    @api.depends('report_instance_id.pivot_date',
                 'report_instance_id.comparison_mode',
                 'type', 'offset', 'duration', 'mode')
    def _compute_dates(self):
        self.date_from = False
        self.date_to = False
        self.valid = False
        report = self.report_instance_id
        d = fields.Date.from_string(report.pivot_date)
        if not report.comparison_mode:
            self.date_from = report.date_from
            self.date_to = report.date_to
            self.valid = True
        elif self.mode == 'fix':
            self.date_from = self.manual_date_from
            self.date_to = self.manual_date_to
            self.valid = True
        elif self.type == 'd':
            date_from = d + datetime.timedelta(days=self.offset)
            date_to = date_from + \
                datetime.timedelta(days=self.duration - 1)
            self.date_from = fields.Date.to_string(date_from)
            self.date_to = fields.Date.to_string(date_to)
            self.valid = True
        elif self.type == 'w':
            date_from = d - datetime.timedelta(d.weekday())
            date_from = date_from + datetime.timedelta(days=self.offset * 7)
            date_to = date_from + \
                datetime.timedelta(days=(7 * self.duration) - 1)
            self.date_from = fields.Date.to_string(date_from)
            self.date_to = fields.Date.to_string(date_to)
            self.valid = True
        elif self.type == 'date_range':
            date_range_obj = self.env['date.range']
            current_periods = date_range_obj.search(
                [('type_id', '=', self.date_range_type_id.id),
                 ('date_start', '<=', d),
                 ('date_end', '>=', d),
                 ('company_id', '=', self.report_instance_id.company_id.id)])
            if current_periods:
                all_periods = date_range_obj.search(
                    [('type_id', '=', self.date_range_type_id.id),
                     ('company_id', '=',
                      self.report_instance_id.company_id.id)],
                    order='date_start')
                all_period_ids = [p.id for p in all_periods]
                p = all_period_ids.index(current_periods[0].id) + self.offset
                if p >= 0 and p + self.duration <= len(all_period_ids):
                    periods = all_periods[p:p + self.duration]
                    self.date_from = periods[0].date_start
                    self.date_to = periods[-1].date_end
                    self.valid = True

    _name = 'mis.report.instance.period'

    name = fields.Char(size=32, required=True,
                       string='Description', translate=True)
    mode = fields.Selection([('fix', 'Fix'),
                             ('relative', 'Relative'),
                             ], required=True,
                            default='fix')
    type = fields.Selection([('d', _('Day')),
                             ('w', _('Week')),
                             ('date_range', _('Date Range'))
                             ],
                            string='Period type')
    date_range_type_id = fields.Many2one(
        comodel_name='date.range.type', string='Date Range Type')
    offset = fields.Integer(string='Offset',
                            help='Offset from current period',
                            default=-1)
    duration = fields.Integer(string='Duration',
                              help='Number of periods',
                              default=1)
    date_from = fields.Date(compute='_compute_dates', string="From")
    date_to = fields.Date(compute='_compute_dates', string="To")
    manual_date_from = fields.Date(string="From")
    manual_date_to = fields.Date(string="To")
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date Range')
    valid = fields.Boolean(compute='_compute_dates',
                           type='boolean',
                           string='Valid')
    sequence = fields.Integer(string='Sequence', default=100)
    report_instance_id = fields.Many2one('mis.report.instance',
                                         string='Report Instance',
                                         ondelete='cascade')
    comparison_column_ids = fields.Many2many(
        comodel_name='mis.report.instance.period',
        relation='mis_report_instance_period_rel',
        column1='period_id',
        column2='compare_period_id',
        string='Compare with')
    normalize_factor = fields.Integer(
        string='Factor',
        help='Factor to use to normalize the period (used in comparison',
        default=1)
    subkpi_ids = fields.Many2many(
        'mis.report.subkpi',
        string="Sub KPI Filter")

    _order = 'sequence, id'

    _sql_constraints = [
        ('duration', 'CHECK (duration>0)',
         'Wrong duration, it must be positive!'),
        ('normalize_factor', 'CHECK (normalize_factor>0)',
         'Wrong normalize factor, it must be positive!'),
        ('name_unique', 'unique(name, report_instance_id)',
         'Period name should be unique by report'),
    ]

    @api.onchange('date_range_id')
    def onchange_date_range(self):
        for record in self:
            record.manual_date_from = record.date_range_id.date_start
            record.manual_date_to = record.date_range_id.date_end
            record.name = record.date_range_id.name

    @api.multi
    def _get_additional_move_line_filter(self):
        """ Prepare a filter to apply on all move lines

        This filter is applied with a AND operator on all
        accounting expression domains. This hook is intended
        to be inherited, and is useful to implement filtering
        on analytic dimensions or operational units.

        Returns an Odoo domain expression (a python list)
        compatible with account.move.line."""
        self.ensure_one()
        return []

    @api.multi
    def _get_additional_query_filter(self, query):
        """ Prepare an additional filter to apply on the query

        This filter is combined to the query domain with a AND
        operator. This hook is intended
        to be inherited, and is useful to implement filtering
        on analytic dimensions or operational units.

        Returns an Odoo domain expression (a python list)
        compatible with the model of the query."""
        self.ensure_one()
        return []

    @api.multi
    def drilldown(self, expr):
        self.ensure_one()
        # TODO FIXME: drilldown by account
        if AEP.has_account_var(expr):
            aep = AEP(self.env)
            aep.parse_expr(expr)
            aep.done_parsing(self.report_instance_id.company_id)
            domain = aep.get_aml_domain_for_expr(
                expr,
                self.date_from, self.date_to,
                self.report_instance_id.target_move,
                self.report_instance_id.company_id)
            domain.extend(self._get_additional_move_line_filter())
            return {
                'name': expr + ' - ' + self.name,
                'domain': domain,
                'type': 'ir.actions.act_window',
                'res_model': 'account.move.line',
                'views': [[False, 'list'], [False, 'form']],
                'view_type': 'list',
                'view_mode': 'list',
                'target': 'current',
            }
        else:
            return False


class MisReportInstance(models.Model):
    """The MIS report instance combines everything to compute
    a MIS report template for a set of periods."""

    @api.one
    @api.depends('date')
    def _compute_pivot_date(self):
        if self.date:
            self.pivot_date = self.date
        else:
            self.pivot_date = fields.Date.context_today(self)

    @api.model
    def _default_company(self):
        return self.env['res.company'].\
            _company_default_get('mis.report.instance')

    _name = 'mis.report.instance'

    name = fields.Char(required=True,
                       string='Name', translate=True)
    description = fields.Char(related='report_id.description',
                              readonly=True)
    date = fields.Date(string='Base date',
                       help='Report base date '
                            '(leave empty to use current date)')
    pivot_date = fields.Date(compute='_compute_pivot_date',
                             string="Pivot date")
    report_id = fields.Many2one('mis.report',
                                required=True,
                                string='Report')
    period_ids = fields.One2many('mis.report.instance.period',
                                 'report_instance_id',
                                 required=True,
                                 string='Periods',
                                 copy=True)
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')],
                                   string='Target Moves',
                                   required=True,
                                   default='posted')
    company_id = fields.Many2one(comodel_name='res.company',
                                 string='Company',
                                 default=_default_company,
                                 required=True)
    landscape_pdf = fields.Boolean(string='Landscape PDF')
    comparison_mode = fields.Boolean(
        compute="_compute_comparison_mode",
        inverse="_inverse_comparison_mode")
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date Range')
    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    temporary = fields.Boolean(default=False)

    @api.multi
    def save_report(self):
        self.ensure_one()
        self.write({'temporary': False})
        action = self.env.ref('mis_builder.mis_report_instance_view_action')
        res = action.read()[0]
        view = self.env.ref('mis_builder.mis_report_instance_view_form')
        res.update({
            'views': [(view.id, 'form')],
            'res_id': self.id,
            })
        return res

    @api.model
    def _vacuum_report(self, hours=24):
        clear_date = fields.Datetime.to_string(
            datetime.datetime.now() - datetime.timedelta(hours=hours))
        reports = self.search([
            ('write_date', '<', clear_date),
            ('temporary', '=', True),
            ])
        _logger.debug('Vacuum %s Temporary MIS Builder Report', len(reports))
        return reports.unlink()

    @api.one
    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = _('%s (copy)') % self.name
        return super(MisReportInstance, self).copy(default)

    def _format_date(self, date):
        # format date following user language
        lang_model = self.env['res.lang']
        lang_id = lang_model._lang_get(self.env.user.lang)
        date_format = lang_model.browse(lang_id).date_format
        return datetime.datetime.strftime(
            fields.Date.from_string(date), date_format)

    @api.multi
    @api.depends('date_from')
    def _compute_comparison_mode(self):
        for instance in self:
            instance.comparison_mode = bool(instance.period_ids) and\
                not bool(instance.date_from)

    @api.multi
    def _inverse_comparison_mode(self):
        for record in self:
            if not record.comparison_mode:
                if not record.date_from:
                    record.date_from = datetime.now()
                if not record.date_to:
                    record.date_to = datetime.now()
                record.period_ids.unlink()
                record.write({'period_ids': [
                    (0, 0, {
                        'name': 'Default',
                        'type': 'd',
                        })
                    ]})
            else:
                record.date_from = None
                record.date_to = None

    @api.onchange('date_range_id')
    def onchange_date_range(self):
        for record in self:
            record.date_from = record.date_range_id.date_start
            record.date_to = record.date_range_id.date_end

    @api.multi
    def preview(self):
        assert len(self) == 1
        view_id = self.env.ref('mis_builder.'
                               'mis_report_instance_result_view_form')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mis.report.instance',
            'res_id': self.id,
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id.id,
            'target': 'current',
        }

    @api.multi
    def print_pdf(self):
        self.ensure_one()
        return {
            'name': 'MIS report instance QWEB PDF report',
            'model': 'mis.report.instance',
            'type': 'ir.actions.report.xml',
            'report_name': 'mis_builder.report_mis_report_instance',
            'report_type': 'qweb-pdf',
            'context': self.env.context,
        }

    @api.multi
    def export_xls(self):
        self.ensure_one()
        return {
            'name': 'MIS report instance XLSX report',
            'model': 'mis.report.instance',
            'type': 'ir.actions.report.xml',
            'report_name': 'mis.report.instance.xlsx',
            'report_type': 'xlsx',
            'context': self.env.context,
        }

    @api.multi
    def display_settings(self):
        assert len(self.ids) <= 1
        view_id = self.env.ref('mis_builder.mis_report_instance_view_form')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mis.report.instance',
            'res_id': self.id if self.id else False,
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(view_id.id, 'form')],
            'view_id': view_id.id,
            'target': 'current',
        }

    @api.multi
    def compute(self):
        self.ensure_one()
        aep = self.report_id._prepare_aep(self.company_id)
        kpi_matrix = self.report_id._prepare_kpi_matrix()
        for period in self.period_ids:
            # add the column header
            if period.date_from == period.date_to:
                comment = self._format_date(period.date_from)
            else:
                # from, to
                date_from = self._format_date(period.date_from)
                date_to = self._format_date(period.date_to)
                comment = _('from %s to %s') % (date_from, date_to)
            self.report_id._declare_and_compute_period(
                kpi_matrix,
                period.id,
                period.name,
                comment,
                aep,
                period.date_from,
                period.date_to,
                self.target_move,
                self.company_id,
                period.subkpi_ids,
                period._get_additional_move_line_filter,
                period._get_additional_query_filter)
            for comparison_column in period.comparison_column_ids:
                kpi_matrix.declare_comparison(period.id, comparison_column.id)
        kpi_matrix.compute_comparisons()
        return kpi_matrix.as_dict()
