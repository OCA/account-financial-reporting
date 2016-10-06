# -*- coding: utf-8 -*-
# © 2014-2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from collections import defaultdict, OrderedDict
import datetime
import dateutil
from itertools import izip
import logging
import re
import time

import pytz

from openerp import api, fields, models, _
from openerp.exceptions import UserError
from openerp.tools.safe_eval import safe_eval

from .aep import AccountingExpressionProcessor as AEP
from .aggregate import _sum, _avg, _min, _max
from .accounting_none import AccountingNone
from .simple_array import SimpleArray
from .mis_safe_eval import mis_safe_eval, DataError, NameDataError
from .mis_report_style import (
    TYPE_NUM, TYPE_PCT, TYPE_STR, CMP_DIFF, CMP_PCT, CMP_NONE
)

_logger = logging.getLogger(__name__)


class AutoStruct(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class KpiMatrixRow(object):

    # TODO: ultimately, the kpi matrix will become ignorant of KPI's and
    #       accounts and know about rows, columns, sub columns and styles only.
    #       It is already ignorant of period and only knowns about columns.
    #       This will require a correct abstraction for expanding row details.

    def __init__(self, matrix, kpi, account_id=None, parent_row=None):
        self._matrix = matrix
        self.kpi = kpi
        self.account_id = account_id
        self.description = ''
        self.parent_row = parent_row
        if not self.account_id:
            self.style_props = self._matrix._style_model.merge([
                self.kpi.report_id.style_id,
                self.kpi.style_id])
        else:
            self.style_props = self._matrix._style_model.merge([
                self.kpi.report_id.style_id,
                self.kpi.auto_expand_accounts_style_id])

    @property
    def label(self):
        if not self.account_id:
            return self.kpi.description
        else:
            return self._matrix.get_account_name(self.account_id)

    @property
    def row_id(self):
        if not self.account_id:
            return self.kpi.name
        else:
            return '{}:{}'.format(self.kpi.name, self.account_id)

    def iter_cell_tuples(self, cols=None):
        if cols is None:
            cols = self._matrix.iter_cols()
        for col in cols:
            yield col.get_cell_tuple_for_row(self)

    def iter_cells(self, subcols=None):
        if subcols is None:
            subcols = self._matrix.iter_subcols()
        for subcol in subcols:
            yield subcol.get_cell_for_row(self)


class KpiMatrixCol(object):

    def __init__(self, label, description, locals_dict, subkpis):
        self.label = label
        self.description = description
        self.locals_dict = locals_dict
        self.colspan = subkpis and len(subkpis) or 1
        self._subcols = []
        self.subkpis = subkpis
        if not subkpis:
            subcol = KpiMatrixSubCol(self, '', '', 0)
            self._subcols.append(subcol)
        else:
            for i, subkpi in enumerate(subkpis):
                subcol = KpiMatrixSubCol(self, subkpi.description, '', i)
                self._subcols.append(subcol)
        self._cell_tuples_by_row = {}  # {row: (cells tuple)}

    def _set_cell_tuple(self, row, cell_tuple):
        self._cell_tuples_by_row[row] = cell_tuple

    def iter_subcols(self):
        return self._subcols

    def iter_cell_tuples(self):
        return self._cell_tuples_by_row.values()

    def get_cell_tuple_for_row(self, row):
        return self._cell_tuples_by_row.get(row)


class KpiMatrixSubCol(object):

    def __init__(self, col, label, description, index=0):
        self.col = col
        self.label = label
        self.description = description
        self.index = index

    @property
    def subkpi(self):
        if self.col.subkpis:
            return self.col.subkpis[self.index]

    def iter_cells(self):
        for cell_tuple in self.col.iter_cell_tuples():
            yield cell_tuple[self.index]

    def get_cell_for_row(self, row):
        cell_tuple = self.col.get_cell_tuple_for_row(row)
        if cell_tuple is None:
            return None
        return cell_tuple[self.index]


class KpiMatrixCell(object):

    def __init__(self, row, subcol,
                 val, val_rendered, val_comment,
                 style_props,
                 drilldown_arg):
        self.row = row
        self.subcol = subcol
        self.val = val
        self.val_rendered = val_rendered
        self.val_comment = val_comment
        self.style_props = style_props
        self.drilldown_arg = drilldown_arg


class KpiMatrix(object):

    def __init__(self, env):
        # cache language id for faster rendering
        lang_model = env['res.lang']
        lang_id = lang_model._lang_get(env.user.lang)
        self.lang = lang_model.browse(lang_id)
        self._style_model = env['mis.report.style']
        self._account_model = env['account.account']
        # data structures
        # { kpi: KpiMatrixRow }
        self._kpi_rows = OrderedDict()
        # { kpi: {account_id: KpiMatrixRow} }
        self._detail_rows = {}
        # { col_key: KpiMatrixCol }
        self._cols = OrderedDict()
        # { col_key (left of comparison): [(col_key, base_col_key)] }
        self._comparison_todo = defaultdict(list)
        self._comparison_cols = defaultdict(list)
        # { account_id: account_name }
        self._account_names = {}

    def declare_kpi(self, kpi):
        """ Declare a new kpi (row) in the matrix.

        Invoke this first for all kpi, in display order.
        """
        self._kpi_rows[kpi] = KpiMatrixRow(self, kpi)
        self._detail_rows[kpi] = {}

    def declare_col(self, col_key, label, description,
                    locals_dict, subkpis):
        """ Declare a new column, giving it an identifier (key).

        Invoke this and declare_comparison in display order.
        """
        col = KpiMatrixCol(label, description, locals_dict, subkpis)
        self._cols[col_key] = col
        return col

    def declare_comparison(self, col_key, base_col_key):
        """ Declare a new comparison column.

        Invoke this and declare_col in display order.
        """
        last_col_key = list(self._cols.keys())[-1]
        self._comparison_todo[last_col_key].append(
            (col_key, base_col_key))

    def set_values(self, kpi, col_key, vals,
                   drilldown_args):
        """ Set values for a kpi and a colum.

        Invoke this after declaring the kpi and the column.
        """
        self.set_values_detail_account(kpi, col_key, None, vals,
                                       drilldown_args)

    def set_values_detail_account(self, kpi, col_key, account_id, vals,
                                  drilldown_args):
        """ Set values for a kpi and a column and a detail account.

        Invoke this after declaring the kpi and the column.
        """
        if not account_id:
            row = self._kpi_rows[kpi]
        else:
            kpi_row = self._kpi_rows[kpi]
            if account_id in self._detail_rows[kpi]:
                row = self._detail_rows[kpi][account_id]
            else:
                row = KpiMatrixRow(self, kpi, account_id, parent_row=kpi_row)
                self._detail_rows[kpi][account_id] = row
        col = self._cols[col_key]
        cell_tuple = []
        assert len(vals) == col.colspan
        assert len(drilldown_args) == col.colspan
        for val, drilldown_arg, subcol in \
                izip(vals, drilldown_args, col.iter_subcols()):
            if isinstance(val, DataError):
                val_rendered = val.name
                val_comment = val.msg
            else:
                val_rendered = self._style_model.render(
                    self.lang, row.style_props, kpi.type, val)
                if subcol.subkpi:
                    val_comment = u'{}.{} = {}'.format(
                        row.kpi.name,
                        subcol.subkpi.name,
                        row.kpi.get_expression_for_subkpi(subcol.subkpi))
                else:
                    val_comment = u'{} = {}'.format(
                        row.kpi.name,
                        row.kpi.expression)
            cell_style_props = row.style_props
            if row.kpi.style_expression:
                # evaluate style expression
                try:
                    style_name = mis_safe_eval(row.kpi.style_expression,
                                               col.locals_dict)
                except:
                    _logger.error("Error evaluating style expression <%s>",
                                  row.kpi.style_expression, exc_info=True)
                if style_name:
                    style = self._style_model.search(
                        [('name', '=', style_name)])
                    if style:
                        cell_style_props = self._style_model.merge(
                            [row.style_props, style[0]])
                    else:
                        _logger.error("Style '%s' not found.", style_name)
            cell = KpiMatrixCell(row, subcol, val, val_rendered, val_comment,
                                 cell_style_props, drilldown_arg)
            cell_tuple.append(cell)
        assert len(cell_tuple) == col.colspan
        col._set_cell_tuple(row, cell_tuple)

    def compute_comparisons(self):
        """ Compute comparisons.

        Invoke this after setting all values.
        """
        for pos_col_key, comparisons in self._comparison_todo.items():
            for col_key, base_col_key in comparisons:
                col = self._cols[col_key]
                base_col = self._cols[base_col_key]
                common_subkpis = set(col.subkpis) & set(base_col.subkpis)
                if (col.subkpis or base_col.subkpis) and not common_subkpis:
                    raise UserError('Columns {} and {} are not comparable'.
                                    format(col.description,
                                           base_col.description))
                label = u'{} vs {}'.\
                    format(col.label, base_col.label)
                comparison_col = KpiMatrixCol(label, None, {},
                                              sorted(common_subkpis,
                                                     key=lambda s: s.sequence))
                for row in self.iter_rows():
                    cell_tuple = col.get_cell_tuple_for_row(row)
                    base_cell_tuple = base_col.get_cell_tuple_for_row(row)
                    if cell_tuple is None and base_cell_tuple is None:
                        continue
                    if cell_tuple is None:
                        vals = [AccountingNone] * \
                            (len(common_subkpis) or 1)
                    else:
                        vals = [cell.val for cell in cell_tuple
                                if not common_subkpis or
                                cell.subcol.subkpi in common_subkpis]
                    if base_cell_tuple is None:
                        base_vals = [AccountingNone] * \
                            (len(common_subkpis) or 1)
                    else:
                        base_vals = [cell.val for cell in base_cell_tuple
                                     if not common_subkpis or
                                     cell.subcol.subkpi in common_subkpis]
                    comparison_cell_tuple = []
                    for val, base_val, comparison_subcol in \
                            izip(vals,
                                 base_vals,
                                 comparison_col.iter_subcols()):
                        # TODO FIXME average factors
                        delta, delta_r, style_r = \
                            self._style_model.compare_and_render(
                                self.lang, row.style_props,
                                row.kpi.type, row.kpi.compare_method,
                                val, base_val, 1, 1)
                        comparison_cell_tuple.append(KpiMatrixCell(
                            row, comparison_subcol, delta, delta_r, None,
                            style_r, None))
                    comparison_col._set_cell_tuple(row, comparison_cell_tuple)
                self._comparison_cols[pos_col_key].append(comparison_col)

    def iter_rows(self):
        """ Iterate rows in display order.

        yields KpiMatrixRow.
        """
        for kpi_row in self._kpi_rows.values():
            yield kpi_row
            detail_rows = self._detail_rows[kpi_row.kpi].values()
            detail_rows = sorted(detail_rows, key=lambda r: r.description)
            for detail_row in detail_rows:
                yield detail_row

    def iter_cols(self):
        """ Iterate columns in display order.

        yields KpiMatrixCol: one for each column or comparison.
        """
        for col_key, col in self._cols.items():
            yield col
            for comparison_col in self._comparison_cols[col_key]:
                yield comparison_col

    def iter_subcols(self):
        """ Iterate sub columns in display order.

        yields KpiMatrixSubCol: one for each subkpi in each column
        and comparison.
        """
        for col in self.iter_cols():
            for subcol in col.iter_subcols():
                yield subcol

    def _load_account_names(self):
        account_ids = set()
        for detail_rows in self._detail_rows.values():
            account_ids.update(detail_rows.keys())
        account_ids = list(account_ids)
        accounts = self._account_model.search([('id', 'in', account_ids)])
        self._account_names = {a.id: u'{} {}'.format(a.code, a.name)
                               for a in accounts}

    def get_account_name(self, account_id):
        if account_id not in self._account_names:
            self._load_account_names()
        return self._account_names[account_id]

    def as_dict(self):
        header = [{'cols': []}, {'cols': []}]
        for col in self.iter_cols():
            header[0]['cols'].append({
                'label': col.label,
                'description': col.description,
                'colspan': col.colspan,
            })
            for subcol in col.iter_subcols():
                header[1]['cols'].append({
                    'label': subcol.label,
                    'description': subcol.description,
                    'colspan': 1,
                })

        body = []
        for row in self.iter_rows():
            row_data = {
                'row_id': row.row_id,
                'parent_row_id': (row.parent_row and
                                  row.parent_row.row_id or None),
                'label': row.label,
                'description': row.description,
                'style': self._style_model.to_css_style(
                    row.style_props),
                'cells': []
            }
            for cell in row.iter_cells():
                if cell is None:
                    # TODO use subcol style here
                    row_data['cells'].append({})
                else:
                    if cell.val is AccountingNone or \
                            isinstance(cell.val, DataError):
                        val = None
                    else:
                        val = cell.val
                    col_data = {
                        'val': val,
                        'val_r': cell.val_rendered,
                        'val_c': cell.val_comment,
                        'style': self._style_model.to_css_style(
                            cell.style_props),
                    }
                    if cell.drilldown_arg:
                        col_data['drilldown_arg'] = cell.drilldown_arg
                    row_data['cells'].append(col_data)
            body.append(row_data)

        return {
            'header': header,
            'body': body,
        }


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
    expression_ids = fields.One2many('mis.report.kpi.expression', 'kpi_id')
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
    sequence = fields.Integer(string='Sequence', default=100)
    report_id = fields.Many2one('mis.report',
                                string='Report',
                                ondelete='cascade')

    _order = 'sequence, id'

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
        elif self.type == TYPE_PCT:
            self.compare_method = CMP_DIFF
        elif self.type == TYPE_STR:
            self.compare_method = CMP_NONE

    def get_expression_for_subkpi(self, subkpi):
        for expression in self.expression_ids:
            if expression.subkpi_id == subkpi:
                return expression.name


class MisReportSubkpi(models.Model):
    _name = 'mis.report.subkpi'
    _order = 'sequence'

    sequence = fields.Integer()
    report_id = fields.Many2one('mis.report')
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

    @api.multi
    def unlink(self):
        for subkpi in self:
            subkpi.expression_ids.unlink()
        return super(MisReportSubkpi, self).unlink()


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
    kpi_id = fields.Many2one('mis.report.kpi')
    # TODO FIXME set readonly=True when onchange('subkpi_ids') below works
    subkpi_id = fields.Many2one(
        'mis.report.subkpi',
        readonly=False)

    _sql_constraints = [
        ('subkpi_kpi_unique', 'unique(subkpi_id, kpi_id)',
         'Sub KPI must be used once and only once for each KPI'),
    ]


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
                               string='Model')
    field_ids = fields.Many2many('ir.model.fields', required=True,
                                 string='Fields to fetch')
    field_names = fields.Char(compute='_compute_field_names',
                              string='Fetched fields name')
    aggregate = fields.Selection([('sum', _('Sum')),
                                  ('avg', _('Average')),
                                  ('min', _('Min')),
                                  ('max', _('Max'))],
                                 string='Aggregate')
    date_field = fields.Many2one('ir.model.fields', required=True,
                                 string='Date field',
                                 domain=[('ttype', 'in',
                                         ('date', 'datetime'))])
    domain = fields.Char(string='Domain')
    report_id = fields.Many2one('mis.report', string='Report',
                                ondelete='cascade')

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
        default = dict(default or {})
        default['name'] = _('%s (copy)') % self.name
        return super(MisReport, self).copy(default)

    # TODO: kpi name cannot be start with query name

    @api.multi
    def prepare_kpi_matrix(self):
        self.ensure_one()
        kpi_matrix = KpiMatrix(self.env)
        for kpi in self.kpi_ids:
            kpi_matrix.declare_kpi(kpi)
        return kpi_matrix

    @api.multi
    def prepare_aep(self, company):
        self.ensure_one()
        aep = AEP(company)
        for kpi in self.kpi_ids:
            for expression in kpi.expression_ids:
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
                                   locals_dict=None):
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
                       additional_move_line_filter)

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
                expressions = []
                for expression in kpi.expression_ids:
                    if expression.subkpi_id and \
                            subkpis_filter and \
                            expression.subkpi_id not in subkpis_filter:
                        continue
                    expressions.append(expression.name)

                vals = []
                drilldown_args = []
                name_error = False
                for expression in expressions:
                    replaced_expr = aep.replace_expr(expression)
                    vals.append(
                        mis_safe_eval(replaced_expr, locals_dict))
                    if isinstance(vals[-1], NameDataError):
                        name_error = True
                    if replaced_expr != expression:
                        drilldown_args.append({
                            'period_id': col_key,
                            'expr': expression,
                        })
                    else:
                        drilldown_args.append(None)
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

                if not kpi.auto_expand_accounts or name_error:
                    continue

                for account_id, replaced_exprs in \
                        aep.replace_exprs_by_account_id(expressions):
                    vals = []
                    drilldown_args = []
                    for expression, replaced_expr in \
                            izip(expressions, replaced_exprs):
                        vals.append(mis_safe_eval(replaced_expr, locals_dict))
                        if replaced_expr != expression:
                            drilldown_args.append({
                                'period_id': col_key,
                                'expr': expression,
                                'account_id': account_id
                            })
                        else:
                            drilldown_args.append(None)
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
