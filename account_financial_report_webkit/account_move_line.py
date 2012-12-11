# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi.
#    Copyright Camptocamp SA 2011
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm
from openerp.tools.translate import _


class AccountMoveLine(orm.Model):
    """Overriding Account move line in order to add last_rec_date.
    Last rec date is the date of the last reconciliation (full or partial) account move line"""
    _inherit = 'account.move.line'

    def init(self, cr):
        ##We do not want to catch error as if sql is not run it will give invalid data
        cr.execute("UPDATE account_move_line as acm "
                   " SET last_rec_date ="
                   "     (SELECT date from account_move_line"
                   "          WHERE reconcile_id =  acm.reconcile_id"
                   "              AND reconcile_id IS NOT NULL"
                   "          ORDER BY date DESC LIMIT 1)"
                   " WHERE last_rec_date is null;")

        cr.execute("UPDATE account_move_line as acm "
                   " SET last_rec_date ="
                   "     (SELECT date from account_move_line"
                   "          WHERE reconcile_partial_id =  acm.reconcile_partial_id"
                   "              AND reconcile_partial_id IS NOT NULL"
                   "          ORDER BY date DESC LIMIT 1)"
                   " WHERE last_rec_date is null;")

    def _get_move_line_from_line_rec(self, cr, uid, ids, context=None):
        moves = []
        for reconcile in self.pool.get('account.move.reconcile').browse(cr, uid, ids, context=context):
            for move_line in reconcile.line_partial_ids:
                moves.append(move_line.id)
            for move_line in reconcile.line_id:
                moves.append(move_line.id)
        return list(set(moves))

    def _get_last_rec_date(self, cursor, uid, ids, name, args, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        res = {}
        for line in self.browse(cursor, uid, ids, context):
            res[line.id] = {'last_rec_date': False}
            rec = line.reconcile_id or line.reconcile_partial_id or False
            if rec:
                # we use cursor in order to gain some perfs
                cursor.execute('SELECT date from account_move_line where'
                              ' reconcile_id = %s OR reconcile_partial_id = %s'
                              ' ORDER BY date DESC LIMIT 1 ',
                              (rec.id, rec.id))
                res_set = cursor.fetchone()
                if res_set:
                    res[line.id] = {'last_rec_date': res_set[0]}
        return res

    _columns = {
                'last_rec_date': fields.function(_get_last_rec_date,
                     method=True,
                     string='Last reconciliation date',
                     store={'account.move.line': (lambda self, cr, uid, ids, c={}: ids, ['date'], 20),
                            'account.move.reconcile': (_get_move_line_from_line_rec, None, 20)},
                     type='date',
                     multi='all',
                     help="the date of the last reconciliation (full or partial) account move line"),
                }
