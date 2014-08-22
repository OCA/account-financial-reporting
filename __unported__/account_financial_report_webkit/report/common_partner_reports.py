# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
#    Copyright Camptocamp SA 2011
#    SQL inspired from OpenERP original code
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
# TODO refactor helper in order to act more like mixin
# By using properties we will have a more simple signature in fuctions

from collections import defaultdict
from datetime import datetime

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from .common_reports import CommonReportHeaderWebkit


class CommonPartnersReportHeaderWebkit(CommonReportHeaderWebkit):

    """Define common helper for partner oriented financial report"""

    ######################################
    # Account move line retrieval helper #
    ######################################

    def get_partners_move_lines_ids(self, account_id, main_filter, start, stop,
                                    target_move,
                                    exclude_reconcile=False,
                                    partner_filter=False):
        filter_from = False
        if main_filter in ('filter_period', 'filter_no'):
            filter_from = 'period'
        elif main_filter == 'filter_date':
            filter_from = 'date'
        if filter_from:
            return self._get_partners_move_line_ids(
                filter_from, account_id, start, stop, target_move,
                exclude_reconcile=exclude_reconcile,
                partner_filter=partner_filter)

    def _get_first_special_period(self):
        """
        Returns the browse record of the period with the `special` flag, which
        is the special period of the first fiscal year used in the accounting.

        i.e. it searches the first fiscal year with at least one journal entry,
        and it returns the id of the first period for which `special` is True
        in this fiscal year.

        It is used for example in the partners reports, where we have to
        include the first, and only the first opening period.

        :return: browse record of the first special period.
        """
        move_line_obj = self.pool.get('account.move.line')
        first_entry_id = move_line_obj.search(
            self.cr, self.uid, [], order='date ASC', limit=1)
        # it means there is no entry at all, that's unlikely to happen, but
        # it may so
        if not first_entry_id:
            return
        first_entry = move_line_obj.browse(
            self.cr, self.uid, first_entry_id[0])
        fiscalyear = first_entry.period_id.fiscalyear_id
        special_periods = [
            period for period in fiscalyear.period_ids if period.special]
        # so, we have no opening period on the first year, nothing to return
        if not special_periods:
            return
        return min(special_periods,
                   key=lambda p: datetime.strptime(p.date_start,
                                                   DEFAULT_SERVER_DATE_FORMAT))

    def _get_period_range_from_start_period(self, start_period,
                                            include_opening=False,
                                            fiscalyear=False,
                                            stop_at_previous_opening=False):
        """We retrieve all periods before start period"""
        periods = super(CommonPartnersReportHeaderWebkit, self).\
            _get_period_range_from_start_period(
                start_period,
                include_opening=include_opening,
                fiscalyear=fiscalyear,
                stop_at_previous_opening=stop_at_previous_opening)
        first_special = self._get_first_special_period()
        if first_special and first_special.id not in periods:
            periods.append(first_special.id)
        return periods

    def _get_query_params_from_periods(self, period_start, period_stop,
                                       mode='exclude_opening'):
        """
        Build the part of the sql "where clause" which filters on the selected
        periods.

        :param browse_record period_start: first period of the report to print
        :param browse_record period_stop: last period of the report to print
        :param str mode: deprecated
        """
        # we do not want opening period so we exclude opening
        periods = self.pool.get('account.period').build_ctx_periods(
            self.cr, self.uid, period_start.id, period_stop.id)
        if not periods:
            return []

        if mode != 'include_opening':
            periods = self.exclude_opening_periods(periods)

        search_params = {'period_ids': tuple(periods),
                         'date_stop': period_stop.date_stop}

        sql_conditions = ""
        if periods:
            sql_conditions = "  AND account_move_line.period_id in \
                                                                %(period_ids)s"

        return sql_conditions, search_params

    def _get_query_params_from_dates(self, date_start, date_stop, **args):
        """
        Build the part of the sql where clause based on the dates to print.

        :param str date_start: start date of the report to print
        :param str date_stop: end date of the report to print
        """

        periods = self._get_opening_periods()
        if not periods:
            periods = (-1,)

        search_params = {'period_ids': tuple(periods),
                         'date_start': date_start,
                         'date_stop': date_stop}

        sql_conditions = "  AND account_move_line.period_id not \
                                                            in %(period_ids)s \
                            AND account_move_line.date between \
                                date(%(date_start)s) and date((%(date_stop)s))"

        return sql_conditions, search_params

    def _get_partners_move_line_ids(self, filter_from, account_id, start, stop,
                                    target_move,
                                    opening_mode='exclude_opening',
                                    exclude_reconcile=False,
                                    partner_filter=None):
        """

        :param str filter_from: "periods" or "dates"
        :param int account_id: id of the account where to search move lines
        :param str or browse_record start: start date or start period
        :param str or browse_record stop: stop date or stop period
        :param str target_move: 'posted' or 'all'
        :param opening_mode: deprecated
        :param boolean exclude_reconcile: wether the reconciled entries are
            filtred or not
        :param list partner_filter: list of partner ids, will filter on their
            move lines
        """

        final_res = defaultdict(list)

        sql_select = "SELECT account_move_line.id, \
                        account_move_line.partner_id FROM account_move_line"
        sql_joins = ''
        sql_where = " WHERE account_move_line.account_id = %(account_ids)s " \
                    " AND account_move_line.state = 'valid' "

        method = getattr(self, '_get_query_params_from_' + filter_from + 's')
        sql_conditions, search_params = method(start, stop)

        sql_where += sql_conditions

        if exclude_reconcile:
            sql_where += ("  AND ((account_move_line.reconcile_id IS NULL)"
                          "   OR (account_move_line.reconcile_id IS NOT NULL \
                              AND account_move_line.last_rec_date > \
                                                      date(%(date_stop)s)))")

        if partner_filter:
            sql_where += "   AND account_move_line.partner_id \
                                                            in %(partner_ids)s"

        if target_move == 'posted':
            sql_joins += "INNER JOIN account_move \
                                ON account_move_line.move_id = account_move.id"
            sql_where += " AND account_move.state = %(target_move)s"
            search_params.update({'target_move': target_move})

        search_params.update({
            'account_ids': account_id,
            'partner_ids': tuple(partner_filter),
        })

        sql = ' '.join((sql_select, sql_joins, sql_where))
        self.cursor.execute(sql, search_params)
        res = self.cursor.dictfetchall()
        if res:
            for row in res:
                final_res[row['partner_id']].append(row['id'])
        return final_res

    def _get_clearance_move_line_ids(self, move_line_ids, date_stop,
                                     date_until):
        if not move_line_ids:
            return []
        move_line_obj = self.pool.get('account.move.line')
        # we do not use orm in order to gain perfo
        # In this case I have to test the effective gain over an itteration
        # Actually ORM does not allows distinct behavior
        sql = "Select distinct reconcile_id from account_move_line \
               where id in %s"
        self.cursor.execute(sql, (tuple(move_line_ids),))
        rec_ids = self.cursor.fetchall()
        if rec_ids:
            rec_ids = [x[0] for x in rec_ids]
            l_ids = move_line_obj.search(self.cursor,
                                         self.uid,
                                         [('reconcile_id', 'in', rec_ids),
                                          ('date', '>=', date_stop),
                                          ('date', '<=', date_until)])
            return l_ids
        else:
            return []

    ##############################################
    # Initial Partner Balance helper             #
    ##############################################

    def _tree_move_line_ids(self, move_lines_data, key=None):
        """
        move_lines_data must be a list of dict which contains at least keys :
         - account_id
         - partner_id
         - other keys with values of the line
         - if param key is defined, only this key will be inserted in the tree
         returns a tree like
         res[account_id.1][partner_id.1][move_line.1,
                                         move_line.2]
                          [partner_id.2][move_line.3]
         res[account_id.2][partner_id.1][move_line.4]
        """
        res = defaultdict(dict)
        for row in move_lines_data[:]:
            account_id = row.pop('account_id')
            partner_id = row.pop('partner_id')
            if key:
                res[account_id].setdefault(partner_id, []).append(row[key])
            else:
                res[account_id][partner_id] = row
        return res

    def _partners_initial_balance_line_ids(self, account_ids, start_period,
                                           partner_filter,
                                           exclude_reconcile=False,
                                           force_period_ids=False,
                                           date_stop=None):
        # take ALL previous periods
        period_ids = force_period_ids \
            if force_period_ids \
            else self._get_period_range_from_start_period(
                start_period, fiscalyear=False, include_opening=False)

        if not period_ids:
            period_ids = [-1]
        search_param = {
            'date_start': start_period.date_start,
            'period_ids': tuple(period_ids),
            'account_ids': tuple(account_ids),
        }
        sql = ("SELECT ml.id, ml.account_id, ml.partner_id "
               "FROM account_move_line ml "
               "INNER JOIN account_account a "
               "ON a.id = ml.account_id "
               "WHERE ml.period_id in %(period_ids)s "
               "AND ml.account_id in %(account_ids)s ")
        if exclude_reconcile:
            if not date_stop:
                raise Exception(
                    "Missing \"date_stop\" to compute the open invoices.")
            search_param.update({'date_stop': date_stop})
            sql += ("AND ((ml.reconcile_id IS NULL) "
                    "OR (ml.reconcile_id IS NOT NULL \
                    AND ml.last_rec_date > date(%(date_stop)s))) ")
        if partner_filter:
            sql += "AND ml.partner_id in %(partner_ids)s "
            search_param.update({'partner_ids': tuple(partner_filter)})

        self.cursor.execute(sql, search_param)
        return self.cursor.dictfetchall()

    def _compute_partners_initial_balances(self, account_ids, start_period,
                                           partner_filter=None,
                                           exclude_reconcile=False,
                                           force_period_ids=False):
        """We compute initial balance.
        If form is filtered by date all initial balance are equal to 0
        This function will sum pear and apple in currency amount if account
        as no secondary currency"""
        if isinstance(account_ids, (int, long)):
            account_ids = [account_ids]
        move_line_ids = self._partners_initial_balance_line_ids(
            account_ids, start_period, partner_filter,
            exclude_reconcile=exclude_reconcile,
            force_period_ids=force_period_ids)
        if not move_line_ids:
            move_line_ids = [{'id': -1}]
        sql = ("SELECT ml.account_id, ml.partner_id,"
               "       sum(ml.debit) as debit, sum(ml.credit) as credit,"
               "       sum(ml.debit-ml.credit) as init_balance,"
               "       CASE WHEN a.currency_id ISNULL THEN 0.0\
                       ELSE sum(ml.amount_currency) \
                       END as init_balance_currency, "
               "       c.name as currency_name "
               "FROM account_move_line ml "
               "INNER JOIN account_account a "
               "ON a.id = ml.account_id "
               "LEFT JOIN res_currency c "
               "ON c.id = a.currency_id "
               "WHERE ml.id in %(move_line_ids)s "
               "GROUP BY ml.account_id, ml.partner_id, a.currency_id, c.name")
        search_param = {
            'move_line_ids': tuple([move_line['id'] for move_line in
                                    move_line_ids])}
        self.cursor.execute(sql, search_param)
        res = self.cursor.dictfetchall()
        return self._tree_move_line_ids(res)

    ############################################################
    # Partner specific helper                                  #
    ############################################################

    def _order_partners(self, *args):
        """We get the partner linked to all current accounts that are used.
            We also use ensure that partner are ordered by name
            args must be list"""
        res = []
        partner_ids = []
        for arg in args:
            if arg:
                partner_ids += arg
        if not partner_ids:
            return []

        existing_partner_ids = [
            partner_id for partner_id in partner_ids if partner_id]
        if existing_partner_ids:
            # We may use orm here as the performance optimization is not that
            # big
            sql = ("SELECT name|| ' ' ||CASE WHEN ref IS NOT NULL \
                                THEN '('||ref||')' \
                                ELSE '' END, id, ref, name"
                   "  FROM res_partner \
                      WHERE id IN %s ORDER BY LOWER(name), ref")
            self.cursor.execute(sql, (tuple(set(existing_partner_ids)),))
            res = self.cursor.fetchall()

        # move lines without partners, set None for empty partner
        if not all(partner_ids):
            res.append((None, None, None, None))

        if not res:
            return []
        return res
