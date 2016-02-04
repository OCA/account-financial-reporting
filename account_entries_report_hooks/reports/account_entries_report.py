# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import models, tools


class AccountEntriesReport(models.Model):
    _inherit = "account.entries.report"

    def _select(self):
        select_str = """
        SELECT
            l.id as id,
            am.date as date,
            l.date_maturity as date_maturity,
            l.date_created as date_created,
            am.ref as ref,
            am.state as move_state,
            l.state as move_line_state,
            l.reconcile_id as reconcile_id,
            l.partner_id as partner_id,
            l.product_id as product_id,
            l.product_uom_id as product_uom_id,
            am.company_id as company_id,
            am.journal_id as journal_id,
            p.fiscalyear_id as fiscalyear_id,
            am.period_id as period_id,
            l.account_id as account_id,
            l.analytic_account_id as analytic_account_id,
            a.type as type,
            a.user_type as user_type,
            1 as nbr,
            l.quantity as quantity,
            l.currency_id as currency_id,
            l.amount_currency as amount_currency,
            l.debit as debit,
            l.credit as credit,
            coalesce(l.debit, 0.0) - coalesce(l.credit, 0.0) as balance
        """
        return select_str

    def _from(self):
        from_str = """
        FROM
            account_move_line l
            left join account_account a on (l.account_id = a.id)
            left join account_move am on (am.id=l.move_id)
            left join account_period p on (am.period_id=p.id)
            
        """
        return from_str

    def _where(self):
        where_str = """
        where l.state != 'draft'
        """
        return where_str

    def _group_by(self):
        group_by_str = """
           """
        return group_by_str

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            %s
            %s
            %s
            )""" % (self._table, self._select(), self._from(), self._where(),
                    self._group_by()))
