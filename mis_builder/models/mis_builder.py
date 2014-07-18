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
from lxml import etree

from openerp.osv import orm, fields
from openerp.tools.safe_eval import safe_eval
from openerp.tools.translate import _
from openerp import tools


class AutoStruct(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _get_selection_label(selection, value):
    for v, l in selection:
        if v == value:
            return l
    return ''


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
                                     ('1e3', _('k')),
                                     ('1e6', _('M'))],
                                    string='Factor'),
        'dp': fields.integer(string='Rounding'),
        'suffix': fields.char(size=16, string='Unit'),
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
    }

    _order = 'sequence'

    # TODO: constraint to check name is a valid python identifier
    # TODO: onchange type pct -> force comparison method = diff
    # TODO: onchange type str -> divider, dp, suffix, compare_method read only

    def _render(self, kpi, value):
        """ render a KPI value as a unicode string, ready for display """
        if kpi.type == 'num':
            return self._render_num(value,
                                    kpi.divider, kpi.dp, kpi.suffix)
        elif kpi.type == 'pct':
            return self._render_num(value,
                                    100, kpi.dp, '%')
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
                return self._render_num(value / base_value - base_value,
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

    _columns = {
        'name': fields.char(size=32, required=True,
                            string='Name'),
        'model_id': fields.many2one('ir.model', required=True,
                                    string='Model'),
        'field_ids': fields.many2many('ir.model.fields', required=True,
                                      string='Fields to fetch'),
        'date_field': fields.many2one('ir.model.fields', required=True,
                                      string='Date field',
                                      domain=[('ttype', 'in', ('date', 'datetime'))]),
        'domain': fields.char(string='Domain'),
        'report_id': fields.many2one('mis.report', string='Report'),
    }

    _order = 'name'


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
                # TODO: filter on company_id
                # TODO: date!
                period_obj = self.pool['account.period']
                all_period_ids = period_obj.search(cr, uid,
                                                   [('special', '=', False)],
                                                   order='date_start',
                                                   context=context)
                current_period_ids = period_obj.search(cr, uid,
                                                       [('special', '=', False),
                                                        ('date_start', '<=', d),
                                                        ('date_stop', '>=', d)],
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
                            string='Name', translate=True),
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
    }

    _defaults = {
        'offset':-1,
        'duration': 1,
    }

    _order = 'sequence'

    # TODO: constraint duration >= 1

    def _fetch_balances(self, cr, uid, c, context=None):
        """ fetch the general account balances for the given period

        returns a dictionary {bal_<account.code>: account.balance}
        """
        account_obj = self.pool['account.account']

        search_ctx = dict(context)
        if c.period_from:
            search_ctx.update({'period_from': c.period_from,
                               'period_to': c.period_to})
        else:
            search_ctx.update({'date_from': c.date_from,
                               'date_to': c.date_to})

        # TODO: initial balance?
        # TODO: draft or posted?
        account_ids = account_obj.search(cr, uid, [])
        account_datas = account_obj.read(cr, uid, account_ids,
                                         ['code', 'balance'],
                                         context=search_ctx)
        balances = {}

        for account_data in account_datas:
            # TODO: normalize code (strip special chars)
            # TODO: company_id in key
            key = 'bal_' + account_data['code']
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
                # TODO: datetime support (convert date to utc midnight)
                # datetime_from = utc_midnight(date_from)
                # datetime_to = utc_midnight(date_to + 1)
                # domain.extend([(query.date_field.name, '>=', datetime_from),
                #                (query.date_field.name, '<', datetime_to)])
                raise orm.except_orm(_('Error!'), _('Not implemented'))
            field_names = [field.name for field in query.field_ids]
            obj_ids = obj.search(cr, uid, domain,
                                 context=context)
            obj_datas = obj.read(cr, uid, obj_ids, field_names,
                                 context=context)
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

        for kpi in c.report_instance_id.report.kpi_ids:
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

    # TODO: mechanism to add comparison columns

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
    }

    def compute(self, cr, uid, _ids, context=None):
        assert isinstance(_ids, (int, long))

        r = self.browse(cr, uid, _ids, context=context)

        res = {}

        rows = []
        for kpi in r.report_id.kpi_ids:
            rows.append(dict(name=kpi.name,
                             description=kpi.description))
        res['rows'] = rows

        cols = []
        for period in r.period_ids:
            col = dict(name=period.name)
        res['cols'] = cols

        return res
