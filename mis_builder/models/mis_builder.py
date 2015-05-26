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

from datetime import datetime, timedelta
from dateutil import parser
import re
import traceback

import pytz
from openerp import api
from openerp.api import Environment
from openerp.osv import orm, fields
from openerp import tools
from openerp.tools.safe_eval import safe_eval
from openerp.tools.translate import _

from .aep import AccountingExpressionProcessor as AEP


class AutoStruct(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _get_selection_label(selection, value):
    for v, l in selection:
        if v == value:
            return l
    return ''


def _utc_midnight(d, tz_name, add_day=0):
    d = datetime.strptime(d, tools.DEFAULT_SERVER_DATE_FORMAT)
    if add_day:
        d = d + timedelta(days=add_day)
    utc_tz = pytz.timezone('UTC')
    context_tz = pytz.timezone(tz_name)
    local_timestamp = context_tz.localize(d, is_dst=False)
    return datetime.strftime(local_timestamp.astimezone(utc_tz),
                             tools.DEFAULT_SERVER_DATETIME_FORMAT)


def _python_var(var_str):
    return re.sub(r'\W|^(?=\d)', '_', var_str).lower()


def _is_valid_python_var(name):
    return re.match("[_A-Za-z][_a-zA-Z0-9]*$", name)


class mis_report_kpi(orm.Model):

    """ A KPI is an element (ie a line) of a MIS report.

    In addition to a name and description, it has an expression
    to compute it based on queries defined in the MIS report.
    It also has various informations defining how to render it
    (numeric or percentage or a string, a suffix, divider) and
    how to render comparison of two values of the KPI.
    """

    _name = 'mis.report.kpi'

    _columns = {
        'name': fields.char(size=32, required=True,
                            string='Name'),
        'description': fields.char(required=True,
                                   string='Description',
                                   translate=True),
        'expression': fields.char(required=True,
                                  string='Expression'),
        'default_css_style': fields.char(
            string='Default CSS style'),
        'css_style': fields.char(string='CSS style expression'),
        'type': fields.selection([('num', _('Numeric')),
                                  ('pct', _('Percentage')),
                                  ('str', _('String'))],
                                 required=True,
                                 string='Type'),
        'divider': fields.selection([('1e-6', _('µ')),
                                     ('1e-3', _('m')),
                                     ('1', _('1')),
                                     ('1e3', _('k')),
                                     ('1e6', _('M'))],
                                    string='Factor'),
        'dp': fields.integer(string='Rounding'),
        'suffix': fields.char(size=16, string='Suffix'),
        'compare_method': fields.selection([('diff', _('Difference')),
                                            ('pct', _('Percentage')),
                                            ('none', _('None'))],
                                           required=True,
                                           string='Comparison Method'),
        'sequence': fields.integer(string='Sequence'),
        'report_id': fields.many2one('mis.report', string='Report',
                                     ondelete='cascade'),
    }

    _defaults = {
        'type': 'num',
        'divider': '1',
        'dp': 0,
        'compare_method': 'pct',
        'sequence': 100,
    }

    _order = 'sequence, id'

    def _check_name(self, cr, uid, ids, context=None):
        for record_name in self.read(cr, uid, ids, ['name']):
            if not _is_valid_python_var(record_name['name']):
                return False
        return True

    _constraints = [
        (_check_name, 'The name must be a valid python identifier', ['name']),
    ]

    def onchange_name(self, cr, uid, ids, name, context=None):
        res = {}
        if name and not _is_valid_python_var(name):
            res['warning'] = {
                'title': 'Invalid name %s' % name,
                'message': 'The name must be a valid python identifier'}
        return res

    def onchange_description(self, cr, uid, ids, description, name,
                             context=None):
        """ construct name from description """
        res = {}
        if description and not name:
            res = {'value': {'name': _python_var(description)}}
        return res

    def onchange_type(self, cr, uid, ids, kpi_type, context=None):
        res = {}
        if kpi_type == 'pct':
            res['value'] = {'compare_method': 'diff'}
        elif kpi_type == 'str':
            res['value'] = {'compare_method': 'none',
                            'divider': '',
                            'dp': 0}
        return res

    def _render(self, cr, uid, lang_id, kpi, value, context=None):
        """ render a KPI value as a unicode string, ready for display """
        if kpi.type == 'num':
            return self._render_num(cr, uid, lang_id, value, kpi.divider,
                                    kpi.dp, kpi.suffix, context=context)
        elif kpi.type == 'pct':
            return self._render_num(cr, uid, lang_id, value, 0.01,
                                    kpi.dp, '%', context=context)
        else:
            return unicode(value)

    def _render_comparison(self, cr, uid, lang_id, kpi, value, base_value,
                           average_value, average_base_value, context=None):
        """ render the comparison of two KPI values, ready for display """
        if value is None or base_value is None:
            return ''
        if kpi.type == 'pct':
            return self._render_num(cr, uid, lang_id,
                                    value - base_value,
                                    0.01, kpi.dp,
                                    _('pp'), sign='+',
                                    context=context)
        elif kpi.type == 'num':
            if average_value:
                value = value / float(average_value)
            if average_base_value:
                base_value = base_value / float(average_base_value)
            if kpi.compare_method == 'diff':
                return self._render_num(cr, uid, lang_id,
                                        value - base_value,
                                        kpi.divider, kpi.dp,
                                        kpi.suffix, sign='+',
                                        context=context)
            elif kpi.compare_method == 'pct':
                if round(base_value, kpi.dp) != 0:
                    return self._render_num(cr, uid, lang_id,
                                            value / base_value - 1,
                                            0.01, kpi.dp,
                                            '%', sign='+',
                                            context=context)
        return ''

    def _render_num(self, cr, uid, lang_id, value, divider,
                    dp, suffix, sign='-', context=None):
        divider_label = _get_selection_label(
            self._columns['divider'].selection, divider)
        if divider_label == '1':
            divider_label = ''
        # format number following user language
        value = round(value / float(divider or 1), dp) or 0
        value = self.pool['res.lang'].format(
            cr, uid, lang_id,
            '%%%s.%df' % (sign, dp),
            value,
            grouping=True,
            context=context)
        value = u'%s\N{NO-BREAK SPACE}%s%s' % \
            (value, divider_label, suffix or '')
        value = value.replace('-', u'\N{NON-BREAKING HYPHEN}')
        return value


class mis_report_query(orm.Model):

    """ A query to fetch data for a MIS report.

    A query works on a model and has a domain and list of fields to fetch.
    At runtime, the domain is expanded with a "and" on the date/datetime field.
    """

    _name = 'mis.report.query'

    def _get_field_names(self, cr, uid, ids, name, args, context=None):
        res = {}
        for query in self.browse(cr, uid, ids, context=context):
            field_names = []
            for field in query.field_ids:
                field_names.append(field.name)
            res[query.id] = ', '.join(field_names)
        return res

    def onchange_field_ids(self, cr, uid, ids, field_ids, context=None):
        # compute field_names
        field_names = []
        for field in self.pool.get('ir.model.fields').read(
                cr, uid,
                field_ids[0][2],
                ['name'],
                context=context):
            field_names.append(field['name'])
        return {'value': {'field_names': ', '.join(field_names)}}

    _columns = {
        'name': fields.char(size=32, required=True,
                            string='Name'),
        'model_id': fields.many2one('ir.model', required=True,
                                    string='Model'),
        'field_ids': fields.many2many('ir.model.fields', required=True,
                                      string='Fields to fetch'),
        'field_names': fields.function(_get_field_names, type='char',
                                       string='Fetched fields name',
                                       store={'mis.report.query':
                                              (lambda self, cr, uid, ids, c={}:
                                               ids, ['field_ids'], 20), }),
        'aggregate': fields.selection([('sum', _('Sum')),
                                       ('avg', _('Average')),
                                       ('min', _('Min')),
                                       ('max', _('Max'))],
                                      string='Aggregate'),
        'date_field': fields.many2one('ir.model.fields', required=True,
                                      string='Date field',
                                      domain=[('ttype', 'in',
                                               ('date', 'datetime'))]),
        'domain': fields.char(string='Domain'),
        'report_id': fields.many2one('mis.report', string='Report',
                                     ondelete='cascade'),
    }

    _order = 'name'

    def _check_name(self, cr, uid, ids, context=None):
        for record_name in self.read(cr, uid, ids, ['name']):
            if not _is_valid_python_var(record_name['name']):
                return False
        return True

    _constraints = [
        (_check_name, 'The name must be a valid python identifier', ['name']),
    ]


class mis_report(orm.Model):
    """ A MIS report template (without period information)

    The MIS report holds:
    * a list of explicit queries; the result of each query is
      stored in a variable with same name as a query, containing as list
      of data structures populated with attributes for each fields to fetch;
      when queries have the group by flag and no fields to group, it returns
      a data structure with the summed fields
    * a list of KPI to be evaluated based on the variables resulting
      from the balance and queries (KPI expressions can references queries
      and accounting expression - see AccoutingExpressionProcessor)
    """

    _name = 'mis.report'

    _columns = {
        'name': fields.char(required=True,
                            string='Name', translate=True),
        'description': fields.char(required=False,
                                   string='Description', translate=True),
        'query_ids': fields.one2many('mis.report.query', 'report_id',
                                     string='Queries'),
        'kpi_ids': fields.one2many('mis.report.kpi', 'report_id',
                                   string='KPI\'s'),
    }

    # TODO: kpi name cannot be start with query name


class mis_report_instance_period(orm.Model):

    """ A MIS report instance has the logic to compute
    a report template for a given date period.

    Periods have a duration (day, week, fiscal period) and
    are defined as an offset relative to a pivot date.
    """

    def _get_dates(self, cr, uid, ids, field_names, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}
        for c in self.browse(cr, uid, ids, context=context):
            date_from = False
            date_to = False
            period_ids = None
            valid = False
            d = parser.parse(c.report_instance_id.pivot_date)
            if c.type == 'd':
                date_from = d + timedelta(days=c.offset)
                date_to = date_from + timedelta(days=c.duration - 1)
                date_from = date_from.strftime(
                    tools.DEFAULT_SERVER_DATE_FORMAT)
                date_to = date_to.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
                valid = True
            elif c.type == 'w':
                date_from = d - timedelta(d.weekday())
                date_from = date_from + timedelta(days=c.offset * 7)
                date_to = date_from + timedelta(days=(7 * c.duration) - 1)
                date_from = date_from.strftime(
                    tools.DEFAULT_SERVER_DATE_FORMAT)
                date_to = date_to.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
                valid = True
            elif c.type == 'fp':
                period_obj = self.pool['account.period']
                current_period_ids = period_obj.search(
                    cr, uid,
                    [('special', '=', False),
                     ('date_start', '<=', d),
                     ('date_stop', '>=', d),
                     ('company_id', '=', c.company_id.id)],
                    context=context)
                if current_period_ids:
                    all_period_ids = period_obj.search(
                        cr, uid,
                        [('special', '=', False),
                         ('company_id', '=', c.company_id.id)],
                        order='date_start',
                        context=context)
                    p = all_period_ids.index(current_period_ids[0]) + c.offset
                    if p >= 0 and p + c.duration <= len(all_period_ids):
                        period_ids = all_period_ids[p:p + c.duration]
                        periods = period_obj.browse(cr, uid, period_ids,
                                                    context=context)
                        date_from = periods[0].date_start
                        date_to = periods[-1].date_stop
                        valid = True

            res[c.id] = {
                'date_from': date_from,
                'date_to': date_to,
                'period_from': period_ids and period_ids[0] or False,
                'period_to': period_ids and period_ids[-1] or False,
                'valid': valid,
            }
        return res

    _name = 'mis.report.instance.period'

    _columns = {
        'name': fields.char(size=32, required=True,
                            string='Description', translate=True),
        'type': fields.selection([('d', _('Day')),
                                  ('w', _('Week')),
                                  ('fp', _('Fiscal Period')),
                                  # ('fy', _('Fiscal Year'))
                                  ],
                                 required=True,
                                 string='Period type'),
        'offset': fields.integer(string='Offset',
                                 help='Offset from current period'),
        'duration': fields.integer(string='Duration',
                                   help='Number of periods'),
        'date_from': fields.function(_get_dates,
                                     type='date',
                                     multi="dates",
                                     string="From"),
        'date_to': fields.function(_get_dates,
                                   type='date',
                                   multi="dates",
                                   string="To"),
        'period_from': fields.function(_get_dates,
                                       type='many2one', obj='account.period',
                                       multi="dates", string="From period"),
        'period_to': fields.function(_get_dates,
                                     type='many2one', obj='account.period',
                                     multi="dates", string="To period"),
        'valid': fields.function(_get_dates,
                                 type='boolean',
                                 multi='dates', string='Valid'),
        'sequence': fields.integer(string='Sequence'),
        'report_instance_id': fields.many2one('mis.report.instance',
                                              string='Report Instance',
                                              ondelete='cascade'),
        'comparison_column_ids': fields.many2many(
            'mis.report.instance.period',
            'mis_report_instance_period_rel',
            'period_id',
            'compare_period_id',
            string='Compare with'),
        'company_id': fields.related('report_instance_id', 'company_id',
                                     type="many2one", relation="res.company",
                                     string="Company", readonly=True),
        'normalize_factor': fields.integer(
            string='Factor',
            help='Factor to use to normalize the period (used in comparison'),
    }

    _defaults = {
        'offset': -1,
        'duration': 1,
        'sequence': 100,
        'normalize_factor': 1,
    }

    _order = 'sequence, id'

    _sql_constraints = [
        ('duration', 'CHECK (duration>0)',
         'Wrong duration, it must be positive!'),
        ('normalize_factor', 'CHECK (normalize_factor>0)',
         'Wrong normalize factor, it must be positive!'),
        ('name_unique', 'unique(name, report_instance_id)',
         'Period name should be unique by report'),
    ]

    def drilldown(self, cr, uid, _id, expr, context=None):
        if context is None:
            context = {}
        this = self.browse(cr, uid, _id, context=context)[0]
        if AEP.has_account_var(expr):
            env = Environment(cr, uid, context)
            aep = AEP(env)
            aep.parse_expr(expr)
            aep.done_parsing(this.report_instance_id.root_account)
            domain = aep.get_aml_domain_for_expr(
                expr, this.date_from, this.date_to,
                this.period_from, this.period_to,
                this.report_instance_id.target_move)
            return {
                'name': expr + ' - ' + this.name,
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

    def _fetch_queries(self, cr, uid, c, context):
        res = {}
        report = c.report_instance_id.report_id
        for query in report.query_ids:
            obj = self.pool[query.model_id.model]
            domain = query.domain and safe_eval(query.domain) or []
            if query.date_field.ttype == 'date':
                domain.extend([(query.date_field.name, '>=', c.date_from),
                               (query.date_field.name, '<=', c.date_to)])
            else:
                datetime_from = _utc_midnight(
                    c.date_from, context.get('tz', 'UTC'))
                datetime_to = _utc_midnight(
                    c.date_to, context.get('tz', 'UTC'), add_day=1)
                domain.extend([(query.date_field.name, '>=', datetime_from),
                               (query.date_field.name, '<', datetime_to)])
            if obj._columns.get('company_id'):
                domain.extend(['|', ('company_id', '=', False),
                               ('company_id', '=', c.company_id.id)])
            field_names = [f.name for f in query.field_ids]
            if not query.aggregate:
                obj_ids = obj.search(cr, uid, domain, context=context)
                obj_datas = obj.read(
                    cr, uid, obj_ids, field_names, context=context)
                res[query.name] = [AutoStruct(**d) for d in obj_datas]
            elif query.aggregate == 'sum':
                obj_datas = obj.read_group(
                    cr, uid, domain, field_names, [], context=context)
                s = AutoStruct(count=obj_datas[0]['__count'])
                for field_name in field_names:
                    setattr(s, field_name, obj_datas[0][field_name])
                res[query.name] = s
            else:
                obj_ids = obj.search(cr, uid, domain, context=context)
                obj_datas = obj.read(
                    cr, uid, obj_ids, field_names, context=context)
                s = AutoStruct(count=len(obj_datas))
                if query.aggregate == 'min':
                    agg = min
                elif query.aggregate == 'max':
                    agg = max
                elif query.aggregate == 'avg':
                    agg = lambda l: sum(l) / float(len(l))
                for field_name in field_names:
                    setattr(s, field_name,
                            agg([d[field_name] for d in obj_datas]))
                res[query.name] = s
        return res

    def _compute(self, cr, uid, lang_id, c, aep, context=None):
        if context is None:
            context = {}

        kpi_obj = self.pool['mis.report.kpi']

        res = {}

        localdict = {
            'registry': self.pool,
            'sum': sum,
            'min': min,
            'max': max,
            'len': len,
            'avg': lambda l: sum(l) / float(len(l)),
        }
        localdict.update(self._fetch_queries(cr, uid, c,
                                             context=context))

        aep.do_queries(c.date_from, c.date_to,
                       c.period_from, c.period_to,
                       c.report_instance_id.target_move)

        compute_queue = c.report_instance_id.report_id.kpi_ids
        recompute_queue = []
        while True:
            for kpi in compute_queue:
                try:
                    kpi_val_comment = kpi.name + " = " + kpi.expression
                    kpi_eval_expression = aep.replace_expr(kpi.expression)
                    kpi_val = safe_eval(kpi_eval_expression, localdict)
                except ZeroDivisionError:
                    kpi_val = None
                    kpi_val_rendered = '#DIV/0'
                    kpi_val_comment += '\n\n%s' % (traceback.format_exc(),)
                except (NameError, ValueError):
                    recompute_queue.append(kpi)
                    kpi_val = None
                    kpi_val_rendered = '#ERR'
                    kpi_val_comment += '\n\n%s' % (traceback.format_exc(),)
                except:
                    kpi_val = None
                    kpi_val_rendered = '#ERR'
                    kpi_val_comment += '\n\n%s' % (traceback.format_exc(),)
                else:
                    kpi_val_rendered = kpi_obj._render(
                        cr, uid, lang_id, kpi, kpi_val, context=context)

                localdict[kpi.name] = kpi_val
                try:
                    kpi_style = None
                    if kpi.css_style:
                        kpi_style = safe_eval(kpi.css_style, localdict)
                except:
                    kpi_style = None

                drilldown = (kpi_val is not None and
                             AEP.has_account_var(kpi.expression))

                res[kpi.name] = {
                    'val': kpi_val,
                    'val_r': kpi_val_rendered,
                    'val_c': kpi_val_comment,
                    'style': kpi_style,
                    'suffix': kpi.suffix,
                    'dp': kpi.dp,
                    'is_percentage': kpi.type == 'pct',
                    'period_id': c.id,
                    'expr': kpi.expression,
                    'drilldown': drilldown,
                }

            if len(recompute_queue) == 0:
                # nothing to recompute, we are done
                break
            if len(recompute_queue) == len(compute_queue):
                # could not compute anything in this iteration
                # (ie real Value errors or cyclic dependency)
                # so we stop trying
                break
            # try again
            compute_queue = recompute_queue
            recompute_queue = []

        return res


class mis_report_instance(orm.Model):

    """ The MIS report instance combines compute and
    display a MIS report template for a set of periods """

    def _get_pivot_date(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for r in self.browse(cr, uid, ids, context=context):
            if r.date:
                res[r.id] = r.date
            else:
                res[r.id] = fields.date.context_today(self, cr, uid,
                                                      context=context)
        return res

    def _get_root_account(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        account_obj = self.pool['account.account']
        for r in self.browse(cr, uid, ids, context=context):
            account_ids = account_obj.search(
                cr, uid,
                [('parent_id', '=', False),
                 ('company_id', '=', r.company_id.id)],
                context=context)
            if len(account_ids) == 1:
                res[r.id] = account_ids[0]
        return res

    _name = 'mis.report.instance'

    _columns = {
        'name': fields.char(required=True,
                            string='Name', translate=True),
        'description': fields.char(required=False,
                                   string='Description', translate=True),
        'date': fields.date(string='Base date',
                            help='Report base date '
                                 '(leave empty to use current date)'),
        'pivot_date': fields.function(_get_pivot_date,
                                      type='date',
                                      string="Pivot date"),
        'report_id': fields.many2one('mis.report',
                                     required=True,
                                     string='Report'),
        'period_ids': fields.one2many('mis.report.instance.period',
                                      'report_instance_id',
                                      required=True,
                                      string='Periods'),
        'target_move': fields.selection([('posted', 'All Posted Entries'),
                                         ('all', 'All Entries'),
                                         ], 'Target Moves', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'root_account': fields.function(_get_root_account,
                                        type='many2one', obj='account.account',
                                        string="Account chart"),
        'landscape_pdf': fields.boolean(string='Landscape PDF'),
    }

    _defaults = {
        'target_move': 'posted',
        'company_id': lambda s, cr, uid, c:
        s.pool.get('res.company')._company_default_get(
            cr, uid,
            'mis.report.instance',
            context=c)
    }

    def _format_date(self, cr, uid, lang_id, date, context=None):
        # format date following user language
        tformat = self.pool['res.lang'].read(
            cr, uid, lang_id, ['date_format'])[0]['date_format']
        return datetime.strftime(datetime.strptime(
            date,
            tools.DEFAULT_SERVER_DATE_FORMAT),
            tformat)

    def preview(self, cr, uid, _id, context=None):
        view_id = self.pool['ir.model.data'].get_object_reference(
            cr, uid, 'mis_builder', 'mis_report_instance_result_view_form')[1]
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mis.report.instance',
            'res_id': _id[0],
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'target': 'new',
        }

    @api.cr_uid_id_context
    def compute(self, cr, uid, _id, context=None):
        assert isinstance(_id, (int, long))
        if context is None:
            context = {}

        this = self.browse(cr, uid, _id, context=context)

        kpi_obj = self.pool['mis.report.kpi']
        report_instance_period_obj = self.pool['mis.report.instance.period']

        # prepare AccountingExpressionProcessor
        env = Environment(cr, uid, context)
        aep = AEP(env)
        for kpi in this.report_id.kpi_ids:
            aep.parse_expr(kpi.expression)
        aep.done_parsing(this.root_account)

        # fetch user language only once (TODO: is it necessary?)
        lang = self.pool['res.users'].read(
            cr, uid, uid, ['lang'], context=context)['lang']
        if not lang:
            lang = 'en_US'
        lang_id = self.pool['res.lang'].search(
            cr, uid, [('code', '=', lang)], context=context)

        # compute kpi values for each period
        kpi_values_by_period_ids = {}
        for period in this.period_ids:
            if not period.valid:
                continue
            kpi_values = report_instance_period_obj._compute(
                cr, uid, lang_id, period, aep, context=context)
            kpi_values_by_period_ids[period.id] = kpi_values

        # prepare header and content
        header = []
        header.append({
            'kpi_name': '',
            'cols': []
        })
        content = []
        rows_by_kpi_name = {}
        for kpi in this.report_id.kpi_ids:
            rows_by_kpi_name[kpi.name] = {
                'kpi_name': kpi.description,
                'cols': [],
                'default_style': kpi.default_css_style
            }
            content.append(rows_by_kpi_name[kpi.name])

        # populate header and content
        for period in this.period_ids:
            if not period.valid:
                continue
            # add the column header
            header[0]['cols'].append(dict(
                name=period.name,
                date=(period.duration > 1 or period.type == 'w') and
                _('from %s to %s' %
                  (period.period_from and period.period_from.name
                   or self._format_date(cr, uid, lang_id, period.date_from,
                                        context=context),
                   period.period_to and period.period_to.name
                   or self._format_date(cr, uid, lang_id, period.date_to,
                                        context=context)))
                or period.period_from and period.period_from.name or
                period.date_from))
            # add kpi values
            kpi_values = kpi_values_by_period_ids[period.id]
            for kpi_name in kpi_values:
                rows_by_kpi_name[kpi_name]['cols'].append(kpi_values[kpi_name])

            # add comparison columns
            for compare_col in period.comparison_column_ids:
                compare_kpi_values = \
                    kpi_values_by_period_ids.get(compare_col.id)
                if compare_kpi_values:
                    # add the comparison column header
                    header[0]['cols'].append(
                        dict(name='%s vs %s' % (period.name, compare_col.name),
                             date=''))
                    # add comparison values
                    for kpi in this.report_id.kpi_ids:
                        rows_by_kpi_name[kpi.name]['cols'].append(
                            {'val_r': kpi_obj._render_comparison(
                                cr,
                                uid,
                                lang_id,
                                kpi,
                                kpi_values[kpi.name]['val'],
                                compare_kpi_values[kpi.name]['val'],
                                period.normalize_factor,
                                compare_col.normalize_factor,
                                context=context)})

        return {'header': header,
                'content': content}
