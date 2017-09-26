# -*- coding: utf-8 -*-
# Copyright 2014-2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from collections import defaultdict
import datetime
from itertools import izip
import logging
import re
import time

import dateutil
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from .aep import AccountingExpressionProcessor as AEP
from .aggregate import _sum, _avg, _min, _max
from .accounting_none import AccountingNone
from .kpimatrix import KpiMatrix
from .simple_array import SimpleArray
from .mis_safe_eval import mis_safe_eval, DataError, NameDataError
from .mis_report_style import (
    TYPE_NUM, TYPE_PCT, TYPE_STR, CMP_DIFF, CMP_PCT, CMP_NONE
)
from .mis_kpi_data import (
    ACC_SUM, ACC_AVG, ACC_NONE
)

_logger = logging.getLogger(__name__)


class AutoStruct(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _utc_midnight(d, tz_name, add_day=0):
    d = fields.Datetime.from_string(d) + datetime.timedelta(days=add_day)
    utc_tz = pytz.timezone('UTC')
    context_tz = pytz.timezone(tz_name)
    local_timestamp = context_tz.localize(d, is_dst=False)
    return fields.Datetime.to_string(local_timestamp.astimezone(utc_tz))


def _python_var(var_str):
    return re.sub(r'\W|^(?=\d)', '_', var_str).lower()


def _is_valid_python_var(name):
    return re.match("[_A-Za-z][_a-zA-Z0-9]*$", name)


class MisReportKpi(models.Model):
    """ A KPI is an element (ie a line) of a MIS report.

    In addition to a name and description, it has an expression
    to compute it based on queries defined in the MIS report.
    It also has various informations defining how to render it
    (numeric or percentage or a string, a prefix, a suffix, divider) and
    how to render comparison of two values of the KPI.
    KPI's have a sequence and are ordered inside the MIS report.
    """

    _name = 'mis.report.kpi'

    name = fields.Char(size=32, required=True,
                       string='Name')
    description = fields.Char(required=True,
                              string='Description',
                              translate=True)
    multi = fields.Boolean()
    expression = fields.Char(
        compute='_compute_expression',
        inverse='_inverse_expression')
    expression_ids = fields.One2many(
        comodel_name='mis.report.kpi.expression',
        inverse_name='kpi_id',
        copy=True,
    )
    auto_expand_accounts = fields.Boolean(string='Display details by account')
    auto_expand_accounts_style_id = fields.Many2one(
        string="Style for account detail rows",
        comodel_name="mis.report.style",
        required=False
    )
    style_id = fields.Many2one(
        string="Style",
        comodel_name="mis.report.style",
        required=False
    )
    style_expression = fields.Char(
        string='Style expression',
        help='An expression that returns a style depending on the KPI value. '
             'Such style is applied on top of the row style.')
    type = fields.Selection([(TYPE_NUM, _('Numeric')),
                             (TYPE_PCT, _('Percentage')),
                             (TYPE_STR, _('String'))],
                            required=True,
                            string='Value type',
                            default=TYPE_NUM)
    compare_method = fields.Selection([(CMP_DIFF, _('Difference')),
                                       (CMP_PCT, _('Percentage')),
                                       (CMP_NONE, _('None'))],
                                      required=True,
                                      string='Comparison Method',
                                      default=CMP_PCT)
    accumulation_method = fields.Selection(
        [(ACC_SUM, _('Sum')),
         (ACC_AVG, _('Average')),
         (ACC_NONE, _('None'))],
        required=True,
        string="Accumulation Method",
        default=ACC_SUM,
        help="Determines how values of this kpi spanning over a "
             "time period are transformed to match the reporting period. "
             "Sum: values of shorter period are added, "
             "values of longest or partially overlapping periods are "
             "adjusted pro-rata temporis.\n"
             "Average: values of included period are averaged "
             "with a pro-rata temporis weight.",
    )
    sequence = fields.Integer(string='Sequence', default=100)
    report_id = fields.Many2one('mis.report',
                                string='Report',
                                required=True,
                                ondelete='cascade')

    _order = 'sequence, id'

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            name = u'{} / {}'.format(rec.name, rec.description)
            res.append((rec.id, name))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        domain = args or []
        domain += [
            '|',
            ('name', operator, name),
            ('description', operator, name),
        ]
        return self.search(domain, limit=limit).name_get()

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if not _is_valid_python_var(record.name):
                raise UserError(_('The name must be a valid python '
                                  'identifier'))

    @api.onchange('name')
    def _onchange_name(self):
        if self.name and not _is_valid_python_var(self.name):
            return {
                'warning': {
                    'title': 'Invalid name %s' % self.name,
                    'message': 'The name must be a valid python identifier'
                }
            }

    @api.multi
    @api.depends('expression_ids.subkpi_id.name', 'expression_ids.name')
    def _compute_expression(self):
        for kpi in self:
            l = []
            for expression in kpi.expression_ids:
                if expression.subkpi_id:
                    l.append(u'{}\xa0=\xa0{}'.format(
                        expression.subkpi_id.name, expression.name))
                else:
                    l.append(
                        expression.name or 'AccountingNone')
            kpi.expression = ',\n'.join(l)

    @api.multi
    def _inverse_expression(self):
        for kpi in self:
            if kpi.multi:
                raise UserError(_('Can not update a multi kpi from '
                                  'the kpi line'))
            if kpi.expression_ids:
                kpi.expression_ids[0].write({
                    'name': kpi.expression,
                    'subkpi_id': None})
                for expression in kpi.expression_ids[1:]:
                    expression.unlink()
            else:
                kpi.write({
                    'expression_ids': [(0, 0, {
                        'name': kpi.expression
                        })]
                    })

    @api.onchange('multi')
    def _onchange_multi(self):
        for kpi in self:
            if not kpi.multi:
                if kpi.expression_ids:
                    kpi.expression = kpi.expression_ids[0].name
                else:
                    kpi.expression = None
            else:
                expressions = []
                for subkpi in kpi.report_id.subkpi_ids:
                    expressions.append((0, 0, {
                        'name': kpi.expression,
                        'subkpi_id': subkpi.id,
                        }))
                kpi.expression_ids = expressions

    @api.onchange('description')
    def _onchange_description(self):
        """ construct name from description """
        if self.description and not self.name:
            self.name = _python_var(self.description)

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == TYPE_NUM:
            self.compare_method = CMP_PCT
            self.accumulation_method = ACC_SUM
        elif self.type == TYPE_PCT:
            self.compare_method = CMP_DIFF
            self.accumulation_method = ACC_AVG
        elif self.type == TYPE_STR:
            self.compare_method = CMP_NONE
            self.accumulation_method = ACC_NONE

    def _get_expression_str_for_subkpi(self, subkpi):
        e = self._get_expression_for_subkpi(subkpi)
        return e and e.name or ''

    def _get_expression_for_subkpi(self, subkpi):
        for expression in self.expression_ids:
            if expression.subkpi_id == subkpi:
                return expression
        return None

    def _get_expressions(self, subkpis):
        if subkpis and self.multi:
            return [
                self._get_expression_for_subkpi(subkpi)
                for subkpi in subkpis
            ]
        else:
            if self.expression_ids:
                assert len(self.expression_ids) == 1
                assert not self.expression_ids[0].subkpi_id
                return self.expression_ids
            else:
                return [None]


class MisReportSubkpi(models.Model):
    _name = 'mis.report.subkpi'
    _order = 'sequence'

    sequence = fields.Integer(default=1)
    report_id = fields.Many2one(
        comodel_name='mis.report',
        required=True,
        ondelete='cascade',
    )
    name = fields.Char(size=32, required=True,
                       string='Name')
    description = fields.Char(required=True,
                              string='Description',
                              translate=True)
    expression_ids = fields.One2many('mis.report.kpi.expression', 'subkpi_id')

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if not _is_valid_python_var(record.name):
                raise UserError(_('The name must be a valid python '
                                  'identifier'))

    @api.onchange('name')
    def _onchange_name(self):
        if self.name and not _is_valid_python_var(self.name):
            return {
                'warning': {
                    'title': 'Invalid name %s' % self.name,
                    'message': 'The name must be a valid python identifier'
                }
            }

    @api.onchange('description')
    def _onchange_description(self):
        """ construct name from description """
        if self.description and not self.name:
            self.name = _python_var(self.description)


class MisReportKpiExpression(models.Model):
    """ A KPI Expression is an expression of a line of a MIS report Kpi.
    It's used to compute the kpi value.
    """

    _name = 'mis.report.kpi.expression'
    _order = 'sequence, name'

    sequence = fields.Integer(
        related='subkpi_id.sequence',
        store=True,
        readonly=True)
    name = fields.Char(string='Expression')
    kpi_id = fields.Many2one(
        'mis.report.kpi', required=True, ondelete='cascade')
    # TODO FIXME set readonly=True when onchange('subkpi_ids') below works
    subkpi_id = fields.Many2one(
        'mis.report.subkpi',
        readonly=False,
        ondelete='cascade')

    _sql_constraints = [
        ('subkpi_kpi_unique', 'unique(subkpi_id, kpi_id)',
         'Sub KPI must be used once and only once for each KPI'),
    ]

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            if rec.subkpi_id:
                name = u'{}.{}'.format(
                    rec.kpi_id.name, rec.subkpi_id.name)
            else:
                name = rec.kpi_id.display_name
            res.append((rec.id, name))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        # TODO maybe implement negative search operators, although
        #      there is not really a use case for that
        domain = args or []
        if '.' in name:
            kpi_name, subkpi_name = name.split('.', 2)
            domain += [
                ('kpi_id.name', '=', kpi_name),
                ('subkpi_id.name', operator, subkpi_name),
            ]
        else:
            domain += [
                '|',
                ('kpi_id.name', operator, name),
                ('kpi_id.description', operator, name),
            ]
        return self.search(domain, limit=limit).name_get()


class MisReportQuery(models.Model):
    """ A query to fetch arbitrary data for a MIS report.

    A query works on a model and has a domain and list of fields to fetch.
    At runtime, the domain is expanded with a "and" on the date/datetime field.
    """

    _name = 'mis.report.query'

    @api.depends('field_ids')
    def _compute_field_names(self):
        for record in self:
            field_names = [field.name for field in record.field_ids]
            record.field_names = ', '.join(field_names)

    name = fields.Char(size=32, required=True,
                       string='Name')
    model_id = fields.Many2one('ir.model', required=True,
                               string='Model',
                               ondelete='restrict')
    field_ids = fields.Many2many('ir.model.fields', required=True,
                                 string='Fields to fetch')
    field_names = fields.Char(compute='_compute_field_names',
                              string='Fetched fields name')
    aggregate = fields.Selection([('sum', _('Sum')),
                                  ('avg', _('Average')),
                                  ('min', _('Min')),
                                  ('max', _('Max'))],
                                 string='Aggregate')
    date_field = fields.Many2one(
        comodel_name='ir.model.fields',
        required=True,
        domain=[('ttype', 'in', ('date', 'datetime'))],
        ondelete='restrict',
    )
    domain = fields.Char(string='Domain')
    report_id = fields.Many2one(
        comodel_name='mis.report',
        string='Report',
        required=True,
        ondelete='cascade',
    )

    _order = 'name'

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if not _is_valid_python_var(record.name):
                raise UserError(_('The name must be a valid python '
                                  'identifier'))


class MisReport(models.Model):
    """ A MIS report template (without period information)

    The MIS report holds:
    * a list of explicit queries; the result of each query is
      stored in a variable with same name as a query, containing as list
      of data structures populated with attributes for each fields to fetch;
      when queries have an aggregate method and no fields to group, it returns
      a data structure with the aggregated fields
    * a list of KPI to be evaluated based on the variables resulting
      from the accounting data and queries (KPI expressions can references
      queries and accounting expression - see AccoutingExpressionProcessor)
    """

    _name = 'mis.report'

    name = fields.Char(required=True,
                       string='Name', translate=True)
    description = fields.Char(required=False,
                              string='Description', translate=True)
    style_id = fields.Many2one(string="Style",
                               comodel_name="mis.report.style")
    query_ids = fields.One2many('mis.report.query', 'report_id',
                                string='Queries',
                                copy=True)
    kpi_ids = fields.One2many('mis.report.kpi', 'report_id',
                              string='KPI\'s',
                              copy=True)
    subkpi_ids = fields.One2many('mis.report.subkpi', 'report_id',
                                 string="Sub KPI",
                                 copy=True)

    @api.onchange('subkpi_ids')
    def _on_change_subkpi_ids(self):
        """ Update kpi expressions when subkpis change on the report,
        so the list of kpi expressions is always up-to-date """
        for kpi in self.kpi_ids:
            if not kpi.multi:
                continue
            new_subkpis = set([subkpi for subkpi in self.subkpi_ids])
            expressions = []
            for expression in kpi.expression_ids:
                assert expression.subkpi_id  # must be true if kpi is multi
                if expression.subkpi_id not in self.subkpi_ids:
                    expressions.append((2, expression.id, None))  # remove
                else:
                    new_subkpis.remove(expression.subkpi_id)  # no change
            for subkpi in new_subkpis:
                # TODO FIXME this does not work, while the remove above works
                expressions.append((0, None, {
                    'name': False,
                    'subkpi_id': subkpi.id,
                }))  # add empty expressions for new subkpis
            if expressions:
                kpi.expressions_ids = expressions

    @api.multi
    def get_wizard_report_action(self):
        action = self.env.ref('mis_builder.mis_report_instance_view_action')
        res = action.read()[0]
        view = self.env.ref('mis_builder.wizard_mis_report_instance_view_form')
        res.update({
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': {
                'default_report_id': self.id,
                'default_name': self.name,
                'default_temporary': True,
                }
            })
        return res

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or [])
        default['name'] = _('%s (copy)') % self.name
        new = super(MisReport, self).copy(default)
        # after a copy, we have new subkpis, but the expressions
        # subkpi_id fields still point to the original one, so
        # we patch them after copying
        subkpis_by_name = dict((sk.name, sk) for sk in new.subkpi_ids)
        for subkpi in self.subkpi_ids:
            # search expressions linked to subkpis of the original report
            exprs = self.env['mis.report.kpi.expression'].search([
                ('kpi_id.report_id', '=', new.id),
                ('subkpi_id', '=', subkpi.id)])
            # and replace them with references to subkpis of the new report
            exprs.write({'subkpi_id': subkpis_by_name[subkpi.name].id})
        return new

    # TODO: kpi name cannot be start with query name

    @api.multi
    def prepare_kpi_matrix(self):
        self.ensure_one()
        kpi_matrix = KpiMatrix(self.env)
        for kpi in self.kpi_ids:
            kpi_matrix.declare_kpi(kpi)
        return kpi_matrix

    @api.multi
    def _prepare_aep(self, company):
        self.ensure_one()
        aep = AEP(company)
        for kpi in self.kpi_ids:
            for expression in kpi.expression_ids:
                if expression.name:
                    aep.parse_expr(expression.name)
        aep.done_parsing()
        return aep

    def prepare_locals_dict(self):
        return {
            'sum': _sum,
            'min': _min,
            'max': _max,
            'len': len,
            'avg': _avg,
            'AccountingNone': AccountingNone,
            'SimpleArray': SimpleArray,
        }

    @api.multi
    def _fetch_queries(self, date_from, date_to,
                       get_additional_query_filter=None):
        self.ensure_one()
        res = {}
        for query in self.query_ids:
            model = self.env[query.model_id.model]
            eval_context = {
                'env': self.env,
                'time': time,
                'datetime': datetime,
                'dateutil': dateutil,
                # deprecated
                'uid': self.env.uid,
                'context': self.env.context,
            }
            domain = query.domain and \
                safe_eval(query.domain, eval_context) or []
            if get_additional_query_filter:
                domain.extend(get_additional_query_filter(query))
            if query.date_field.ttype == 'date':
                domain.extend([(query.date_field.name, '>=', date_from),
                               (query.date_field.name, '<=', date_to)])
            else:
                datetime_from = _utc_midnight(
                    date_from, self._context.get('tz', 'UTC'))
                datetime_to = _utc_midnight(
                    date_to, self._context.get('tz', 'UTC'), add_day=1)
                domain.extend([(query.date_field.name, '>=', datetime_from),
                               (query.date_field.name, '<', datetime_to)])
            field_names = [f.name for f in query.field_ids]
            all_stored = all([model._fields[f].store for f in field_names])
            if not query.aggregate:
                data = model.search_read(domain, field_names)
                res[query.name] = [AutoStruct(**d) for d in data]
            elif query.aggregate == 'sum' and all_stored:
                # use read_group to sum stored fields
                data = model.read_group(
                    domain, field_names, [])
                s = AutoStruct(count=data[0]['__count'])
                for field_name in field_names:
                    try:
                        v = data[0][field_name]
                    except KeyError:
                        _logger.error('field %s not found in read_group '
                                      'for %s; not summable?',
                                      field_name, model._name)
                        v = AccountingNone
                    setattr(s, field_name, v)
                res[query.name] = s
            else:
                data = model.search_read(domain, field_names)
                s = AutoStruct(count=len(data))
                if query.aggregate == 'min':
                    agg = _min
                elif query.aggregate == 'max':
                    agg = _max
                elif query.aggregate == 'avg':
                    agg = _avg
                elif query.aggregate == 'sum':
                    agg = _sum
                for field_name in field_names:
                    setattr(s, field_name,
                            agg([d[field_name] for d in data]))
                res[query.name] = s
        return res

    def _declare_and_compute_col(self,
                                 kpi_matrix,
                                 col_key,
                                 col_label,
                                 col_description,
                                 subkpis_filter,
                                 locals_dict,
                                 eval_expressions,
                                 eval_expressions_by_account):
        """This is the main computation loop.

        It evaluates the kpis and puts the results in the KpiMatrix.
        Evaluation is done through callback methods so data sources
        can provide their own mean of obtaining the data (eg preset
        kpi values for budget, or alternative move line sources).
        """

        if subkpis_filter:
            subkpis = [subkpi for subkpi in self.subkpi_ids
                       if subkpi in subkpis_filter]
        else:
            subkpis = self.subkpi_ids

        col = kpi_matrix.declare_col(col_key,
                                     col_label, col_description,
                                     locals_dict, subkpis)

        compute_queue = self.kpi_ids
        recompute_queue = []
        while True:
            for kpi in compute_queue:
                # build the list of expressions for this kpi
                expressions = kpi._get_expressions(subkpis)

                vals, drilldown_args, name_error = \
                    eval_expressions(expressions, locals_dict)

                if name_error:
                    recompute_queue.append(kpi)
                else:
                    # no error, set it in locals_dict so it can be used
                    # in computing other kpis
                    if len(expressions) == 1:
                        locals_dict[kpi.name] = vals[0]
                    else:
                        locals_dict[kpi.name] = SimpleArray(vals)

                # even in case of name error we set the result in the matrix
                # so the name error will be displayed if it cannot be
                # resolved by recomputing later

                if len(expressions) == 1 and col.colspan > 1:
                    # here we have one expression for this kpi, but
                    # multiple subkpis (so this kpi is most probably
                    # a sum or other operation on multi-valued kpis)
                    if isinstance(vals[0], tuple):
                        vals = vals[0]
                        assert len(vals) == col.colspan
                    elif isinstance(vals[0], DataError):
                        vals = (vals[0],) * col.colspan
                    else:
                        raise UserError(_("Probably not your fault... but I'm "
                                          "really curious to know how you "
                                          "managed to raise this error so "
                                          "I can handle one more corner "
                                          "case!"))
                if len(drilldown_args) != col.colspan:
                    drilldown_args = [None] * col.colspan

                kpi_matrix.set_values(
                    kpi, col_key, vals, drilldown_args)

                if name_error or \
                        not kpi.auto_expand_accounts or \
                        not eval_expressions_by_account:
                    continue

                for account_id, vals, drilldown_args, name_error in \
                        eval_expressions_by_account(expressions, locals_dict):
                    kpi_matrix.set_values_detail_account(
                        kpi, col_key, account_id, vals, drilldown_args)

            if len(recompute_queue) == 0:
                # nothing to recompute, we are done
                break
            if len(recompute_queue) == len(compute_queue):
                # could not compute anything in this iteration
                # (ie real Name errors or cyclic dependency)
                # so we stop trying
                break
            # try again
            compute_queue = recompute_queue
            recompute_queue = []

    @api.multi
    def declare_and_compute_period(self, kpi_matrix,
                                   col_key,
                                   col_label,
                                   col_description,
                                   aep,
                                   date_from, date_to,
                                   target_move,
                                   subkpis_filter=None,
                                   get_additional_move_line_filter=None,
                                   get_additional_query_filter=None,
                                   locals_dict=None,
                                   aml_model=None):
        """ Evaluate a report for a given period, populating a KpiMatrix.

        :param kpi_matrix: the KpiMatrix object to be populated created
                           with prepare_kpi_matrix()
        :param col_key: the period key to use when populating the KpiMatrix
        :param aep: an AccountingExpressionProcessor instance created
                    using _prepare_aep()
        :param date_from, date_to: the starting and ending date
        :param target_move: all|posted
        :param get_additional_move_line_filter: a bound method that takes
                                                no arguments and returns
                                                a domain compatible with
                                                account.move.line
        :param get_additional_query_filter: a bound method that takes a single
                                            query argument and returns a
                                            domain compatible with the query
                                            underlying model
        :param locals_dict: personalized locals dictionary used as evaluation
                            context for the KPI expressions
        """
        self.ensure_one()

        # prepare the localsdict
        if locals_dict is None:
            locals_dict = {}

        locals_dict.update(self.prepare_locals_dict())

        # fetch non-accounting queries
        locals_dict.update(self._fetch_queries(
            date_from, date_to, get_additional_query_filter))

        # use AEP to do the accounting queries
        additional_move_line_filter = None
        if get_additional_move_line_filter:
            additional_move_line_filter = get_additional_move_line_filter()
        aep.do_queries(date_from, date_to,
                       target_move,
                       additional_move_line_filter,
                       aml_model)

        def eval_expressions(expressions, locals_dict):
            expressions = [e and e.name or 'AccountingNone'
                           for e in expressions]
            vals = []
            drilldown_args = []
            name_error = False
            for expression in expressions:
                val = AccountingNone
                drilldown_arg = None
                if expression:
                    replaced_expr = aep.replace_expr(expression)
                    val = mis_safe_eval(replaced_expr, locals_dict)
                    if isinstance(val, NameDataError):
                        name_error = True
                    if replaced_expr != expression:
                        drilldown_arg = {
                            'period_id': col_key,
                            'expr': expression,
                        }
                vals.append(val)
                drilldown_args.append(drilldown_arg)
            return vals, drilldown_args, name_error

        def eval_expressions_by_account(expressions, locals_dict):
            expressions = [e and e.name or 'AccountingNone'
                           for e in expressions]
            for account_id, replaced_exprs in \
                    aep.replace_exprs_by_account_id(expressions):
                vals = []
                drilldown_args = []
                name_error = False
                for expression, replaced_expr in \
                        izip(expressions, replaced_exprs):
                    vals.append(mis_safe_eval(replaced_expr, locals_dict))
                    if replaced_expr != expression:
                        drilldown_args.append({
                            'period_id': col_key,
                            'expr': expression,
                            'account_id': account_id,
                        })
                    else:
                        drilldown_args.append(None)
                yield account_id, vals, drilldown_args, name_error

        self._declare_and_compute_col(
            kpi_matrix, col_key, col_label, col_description, subkpis_filter,
            locals_dict, eval_expressions, eval_expressions_by_account)

    def get_kpis_by_account_id(self, company):
        """ Return { account_id: set(kpi) } """
        aep = self._prepare_aep(company)
        res = defaultdict(set)
        for kpi in self.kpi_ids:
            for expression in kpi.expression_ids:
                if not expression.name:
                    continue
                account_ids = aep.get_account_ids_for_expr(expression.name)
                for account_id in account_ids:
                    res[account_id].add(kpi)
        return res
