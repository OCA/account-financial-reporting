# vim: set fileencoding=utf-8 :
#==============================================================================
#                                                                             =
#    mis_builder module for OpenERP, Management Information System Builder
#    Copyright (C) 2014 ACSONE SA/NV (<http://acsone.eu>)
#                                                                             =
#    This file is a part of mis_builder
#                                                                             =
#    mis_builder is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#                                                                             =
#    mis_builder is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#                                                                             =
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#                                                                             =
#==============================================================================

from datetime import datetime, timedelta
from dateutil import parser
import traceback
import re
import calendar

from openerp.osv import orm, fields
from openerp.tools.safe_eval import safe_eval
from openerp.tools.translate import _
from openerp import tools
from collections import OrderedDict


class AutoStruct(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _get_selection_label(selection, value):
    for v, l in selection:
        if v == value:
            return l
    return ''


def _utc_midnight(d, add_day=0):
    d = datetime.strptime(d, tools.DEFAULT_SERVER_DATE_FORMAT)
    if add_day:
        d = d + timedelta(days=add_day)
    timestamp = calendar.timegm(d.timetuple())
    d_utc_midnight = datetime.utcfromtimestamp(timestamp)
    return datetime.strftime(d_utc_midnight, tools.DEFAULT_SERVER_DATETIME_FORMAT)


def _clean(varStr):
    return re.sub('\W|^(?=\d)', '_', varStr)


class mis_report_kpi(orm.Model):
    """ A KPI is an element of a MIS report.

    In addition to a name and description, it has an expression
    to compute it based on queries defined in the MIS report.
    It also has various informations defining how to render it
    (numeric or percentage or a string, a suffix, divider) and
    how to render comparison of two values of the KPI.
    KPI are ordered inside the MIS report, as some KPI expressions
    can depend on other KPI that need to be computed before.
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
        'report_id': fields.many2one('mis.report', string='Report'),
    }

    _defaults = {
        'type': 'num',
        'divider': '1',
        'dp': 0,
        'compare_method': 'pct',
        'sequence': 1,
    }

    _order = 'sequence'

    def _check_name(self, cr, uid, ids, context=None):
        for record_name in self.read(cr, uid, ids, ['name']):
            if not re.match("[_A-Za-z][_a-zA-Z0-9]*$", record_name['name']):
                return False
        return True

    _constraints = [
        (_check_name, 'The name must be a valid python identifier', ['name']),
    ]

    def onchange_name(self, cr, uid, ids, name, context=None):
        # check it is a valid python identifier
        res = {}
        if name and not re.match("[_A-Za-z][_a-zA-Z0-9]*$", name):
            res['warning'] = {'title': 'Invalid name', 'message': 'The name must be a valid python identifier'}
        return res

    def onchange_description(self, cr, uid, ids, description, name, context=None):
        # construct name from description
        res = {}
        if description and not name:
            res = {'value': {'name': _clean(description)}}
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

    def _render(self, kpi, value):
        """ render a KPI value as a unicode string, ready for display """
        if kpi.type == 'num':
            return self._render_num(value,
                                    kpi.divider, kpi.dp, kpi.suffix)
        elif kpi.type == 'pct':
            return self._render_num(value,
                                    0.01, kpi.dp, '%')
        else:
            return unicode(value)

    def _render_comparison(self, kpi, value, base_value):
        """ render the comparison of two KPI values, ready for display """
        if value is None or base_value is None:
            return ''
        if kpi.type == 'pct':
            return self._render_num(value - base_value,
                                    0.01, kpi.dp, _('pp'),
                                    sign='+')
        elif kpi.type == 'num':
            if kpi.compare_method == 'diff':
                return self._render_num(value - base_value,
                                        kpi.divider, kpi.dp, kpi.suffix,
                                        sign='+')
            elif kpi.compare_method == 'pct' and base_value != 0:
                return self._render_num(value / base_value - 1,
                                        0.01, kpi.dp, '%',
                                        sign='+')
        return ''

    def _render_num(self, value, divider, dp, suffix, sign='-'):
        divider_label = _get_selection_label(
            self._columns['divider'].selection, divider)
        fmt = '{:%s,.%df}%s%s' % (sign, dp, divider_label, suffix or '')
        value = round(value / float(divider or 1), dp) or 0
        return fmt.format(value)


class mis_report_query(orm.Model):
    """ A query to fetch data for a MIS report.

    A query works on a model and has a domain and list of fields to fetch.
    At runtime, the domain is expanded with a "and" on the date/datetime field.
    """

    _name = 'mis.report.query'

    def _get_field_names(self, cr, uid, ids, name, args, context=None):
        res = {}
        for query in self.browse(cr, uid, ids, context=context):
            field_name = []
            for field in query.field_ids:
                field_name.append(field.name)
            res[query.id] = ', '.join(field_name)
        return res

    _columns = {
        'name': fields.char(size=32, required=True,
                            string='Name'),
        'model_id': fields.many2one('ir.model', required=True,
                                    string='Model'),
        'field_ids': fields.many2many('ir.model.fields', required=True,
                                      string='Fields to fetch'),
        'field_name': fields.function(_get_field_names, type='char', string='Fetched fields name',
                                      store={'mis.report.query':
                                             (lambda self, cr, uid, ids, c={}: ids, ['field_ids'], 20), }),
        'date_field': fields.many2one('ir.model.fields', required=True,
                                      string='Date field',
                                      domain=[('ttype', 'in', ('date', 'datetime'))]),
        'domain': fields.char(string='Domain'),
        'report_id': fields.many2one('mis.report', string='Report'),
    }

    _order = 'name'

    def _check_name(self, cr, uid, ids, context=None):
        for record_name in self.read(cr, uid, ids, ['name']):
            if not re.match("[_A-Za-z][_a-zA-Z0-9]*$", record_name['name']):
                return False
        return True

    _constraints = [
        (_check_name, 'The name must be a valid python identifier', ['name']),
    ]


class mis_report(orm.Model):
    """ A MIS report template (without period information)

    The MIS report holds:
    * an implicit query fetching allow the account balances;
      for each account, the balance is stored in a variable named
      bal_{code} where {code} is the account code
    * a list of explicit queries; the result of each query is
      stored in a variable with same name as a query, containing as list
      of data structures populated with attributes for each fields to fetch
    * a list of KPI to be evaluated based on the variables resulting
      from the balance and queries
    """

    _name = 'mis.report'

    _columns = {
        'name': fields.char(size=32, required=True,
                            string='Name', translate=True),
        'description': fields.char(required=False,
                                   string='Description', translate=True),
        'query_ids': fields.one2many('mis.report.query', 'report_id',
                                     string='Queries'),
        'kpi_ids': fields.one2many('mis.report.kpi', 'report_id',
                                   string='KPI\'s'),
    }


class mis_report_instance_period(orm.Model):
    """ A MIS report instance has the logic to compute
    a report template for a give date period.

    Periods have a duration (day, week, fiscal period) and
    are defined as an offset relative to a pivot date.
    """

    def _get_dates(self, cr, uid, ids, field_names, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}
        for c in self.browse(cr, uid, ids, context=context):
            d = parser.parse(c.report_instance_id.pivot_date)
            if c.type == 'd':
                date_from = d + timedelta(days=c.offset)
                date_to = date_from + timedelta(days=c.duration - 1)
                date_from = date_from.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
                date_to = date_to.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
                period_ids = None
            elif c.type == 'w':
                date_from = d - timedelta(d.weekday())
                date_from = date_from + timedelta(days=c.offset * 7)
                date_to = date_from + timedelta(days=(7 * c.duration) - 1)
                date_from = date_from.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
                date_to = date_to.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
                period_ids = None
            elif c.type == 'fp':
                period_obj = self.pool['account.period']
                all_period_ids = period_obj.search(cr, uid,
                                                   [('special', '=', False), ('company_id', '=', c.company_id.id)],
                                                   order='date_start',
                                                   context=context)
                current_period_ids = period_obj.search(cr, uid,
                                                       [('special', '=', False),
                                                        ('date_start', '<=', d),
                                                        ('date_stop', '>=', d),
                                                        ('company_id', '=', c.company_id.id)],
                                                       context=context)
                if not current_period_ids:
                    raise orm.except_orm(_("Error!"),
                                         _("No current fiscal period for %s") % d)
                p = all_period_ids.index(current_period_ids[0]) + c.offset
                if p < 0 or p >= len(all_period_ids):
                    raise orm.except_orm(_("Error!"),
                                         _("No such fiscal period for %s "
                                           "with offset %d") % (d, c.offset))
                period_ids = all_period_ids[p:p + c.duration]
                periods = period_obj.browse(cr, uid, period_ids,
                                            context=context)
                date_from = periods[0].date_start
                date_to = periods[-1].date_stop
            else:
                raise orm.except_orm(_("Error!"),
                                     _("Unimplemented period type %s") %
                                     (c.type,))
            res[c.id] = {
                'date_from': date_from,
                'date_to': date_to,
                'period_from': period_ids and period_ids[0],
                'period_to': period_ids and period_ids[-1],
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
        'sequence': fields.integer(string='Sequence'),
        'report_instance_id': fields.many2one('mis.report.instance',
                                              string='Report Instance'),
        'comparison_column_ids': fields.many2many('mis.report.instance.period', 'mis_report_instance_period_rel',
                                                  'period_id', 'compare_period_id', string='Compare with'),
        'company_id': fields.many2one('res.company', 'Company', required=True)
    }

    _defaults = {
        'offset': -1,
        'duration': 1,
        'sequence': 1,
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid,
                                                                                           'mis.report.instance.period',
                                                                                           context=c)
    }

    _order = 'sequence'

    _sql_constraints = [
        ('duration', 'CHECK (duration>0)', 'Wrong duration, it must be positive!'),
        ('name_unique', 'unique(name, report_instance_id)', 'Period name should be unique by report'),
    ]

    def _fetch_balances(self, cr, uid, c, context=None):
        """ fetch the general account balances for the given period

        returns a dictionary {bal_<account.code>: account.balance}
        """
        if context is None:
            context = {}
        account_obj = self.pool['account.account']

        search_ctx = dict(context)
        if c.period_from:
            search_ctx.update({'period_from': c.period_from.id,
                               'period_to': c.period_to.id})
        else:
            search_ctx.update({'date_from': c.date_from,
                               'date_to': c.date_to})

        # TODO: initial balance?
        account_ids = account_obj.search(cr, uid, [('company_id', '=', c.company_id.id)], context=context)
        account_datas = account_obj.read(cr, uid, account_ids, ['code', 'balance'], context=search_ctx)
        balances = {}
        for account_data in account_datas:
            key = 'bal' + _clean(account_data['code'])
            assert key not in balances
            balances[key] = account_data['balance']

        return balances

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
                datetime_from = _utc_midnight(c.date_from)
                datetime_to = _utc_midnight(c.date_to, add_day=1)
                domain.extend([(query.date_field.name, '>=', datetime_from),
                               (query.date_field.name, '<', datetime_to)])
            if obj._columns.get('company_id', False):
                domain.extend([('company_id', '=', c.company_id.id)])
            field_names = [field.name for field in query.field_ids]
            obj_ids = obj.search(cr, uid, domain, context=context)
            obj_datas = obj.read(cr, uid, obj_ids, field_names, context=context)
            res[query.name] = [AutoStruct(**d) for d in obj_datas]

        return res

    def _compute(self, cr, uid, c, context=None):
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
        localdict.update(self._fetch_balances(cr, uid, c, context=context))
        localdict.update(self._fetch_queries(cr, uid, c, context=context))

        for kpi in c.report_instance_id.report_id.kpi_ids:
            try:
                kpi_val = safe_eval(kpi.expression, localdict)
            except ZeroDivisionError:
                kpi_val = None
                kpi_val_rendered = '#DIV/0'
                kpi_val_comment = traceback.format_exc()
            except:
                kpi_val = None
                kpi_val_rendered = '#ERR'
                kpi_val_comment = traceback.format_exc()
            else:
                kpi_val_rendered = kpi_obj._render(kpi, kpi_val)
                kpi_val_comment = None

            localdict[kpi.name] = kpi_val

            res[kpi.name] = {
                'val': kpi_val,
                'val_r': kpi_val_rendered,
                'val_c': kpi_val_comment,
            }

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

    _name = 'mis.report.instance'

    _columns = {
        'name': fields.char(size=32, required=True,
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
    }

    _defaults = {
            'target_move': 'posted',
    }

    def _format_date(self, cr, uid, date, context=None):
        # format date following user language
        lang = self.pool['res.users'].read(cr, uid, uid, ['lang'], context=context)['lang']
        language_id = self.pool['res.lang'].search(cr, uid, [('code', '=', lang)], context=context)[0]
        tformat = self.pool['res.lang'].read(cr, uid, language_id, ['date_format'])['date_format']
        return datetime.strftime(datetime.strptime(date, tools.DEFAULT_SERVER_DATE_FORMAT), tformat)

    def compute(self, cr, uid, _ids, context=None):
        assert isinstance(_ids, (int, long))
        if context is None:
            context = {}
        r = self.browse(cr, uid, _ids, context=context)
        context['state'] = r.target_move

        content = OrderedDict()
        #empty line name for header
        header = OrderedDict()
        header[''] = {'kpi_name': '', 'cols': []}

        #initialize lines with kpi
        for kpi in r.report_id.kpi_ids:
            content[kpi.name] = {'kpi_name': kpi.description, 'cols': []}

        report_instance_period_obj = self.pool.get('mis.report.instance.period')
        kpi_obj = self.pool.get('mis.report.kpi')

        period_values = {}

        for period in r.period_ids:
            # add the column header
            header['']['cols'].append(dict(name=period.name,
                                           date=period.duration > 1 and
                                           _('from %s to %s' %
                                             (period.period_from and period.period_from.name
                                              or self._format_date(cr, uid, period.date_from, context=context),
                                              period.period_to and period.period_to.name
                                              or self._format_date(cr, uid, period.date_to, context=context)))
                                           or period.period_from and period.period_from.name or period.date_from))
            # compute kpi values
            values = report_instance_period_obj._compute(cr, uid, period, context=context)
            period_values[period.name] = values
            for key in values:
                content[key]['cols'].append(values[key])

        # add comparison column
        for period in r.period_ids:
            for compare_col in period.comparison_column_ids:
                # add the column header
                header['']['cols'].append(dict(name='%s - %s' % (period.name, compare_col.name), date=''))
                column1_values = period_values[period.name]
                column2_values = period_values[compare_col.name]
                for kpi in r.report_id.kpi_ids:
                    content[kpi.name]['cols'].append({'val_r': kpi_obj._render_comparison(kpi,
                                                                                      column1_values[kpi.name]['val'],
                                                                                      column2_values[kpi.name]['val'])})

        return {'header': header,
                'content': content}
