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


def migrate(cr, version):
    if not version:
        # only run at first install
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
                   "          WHERE reconcile_partial_id"
                   "                             = acm.reconcile_partial_id"
                   "              AND reconcile_partial_id IS NOT NULL"
                   "          ORDER BY date DESC LIMIT 1)"
                   " WHERE last_rec_date is null;")
