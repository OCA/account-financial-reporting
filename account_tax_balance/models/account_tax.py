# © 2016 Lorenzo Battistini - Agile Business Group
# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    balance = fields.Float(
        string="Total Balance", compute="_compute_balance",
    )
    base_balance = fields.Float(
        string="Total Base Balance", compute="_compute_balance",
    )
    balance_regular = fields.Float(
        string="Balance", compute="_compute_balance",
    )
    base_balance_regular = fields.Float(
        string="Base Balance", compute="_compute_balance",
    )
    balance_refund = fields.Float(
        string="Balance Refund", compute="_compute_balance",
    )
    base_balance_refund = fields.Float(
        string="Base Balance Refund", compute="_compute_balance",
    )

    def get_context_values(self):
        context = self.env.context
        return (
            context.get('from_date', fields.Date.context_today(self)),
            context.get('to_date', fields.Date.context_today(self)),
            context.get('company_id', self.env.user.company_id.id),
            context.get('target_move', 'posted'),
        )

    @api.model
    def _is_unsupported_search_operator(self, operator):
        return operator != '='

    def _compute_balance(self):
        total_balance_regular = self.compute_balance(
            tax_or_base="tax", move_type="regular"
        )
        total_base_balance_regular = self.compute_balance(
            tax_or_base="base", move_type="regular"
        )
        total_balance_refund = self.compute_balance(
            tax_or_base="tax", move_type="refund"
        )
        total_base_balance_refund = self.compute_balance(
            tax_or_base="base", move_type="refund"
        )
        for tax in self:
            tax.balance_regular = (
                total_balance_regular[tax.id]
                if tax.id in total_balance_regular.keys()
                else 0.0
            )
            tax.base_balance_regular = (
                total_base_balance_regular[tax.id]
                if tax.id in total_base_balance_regular.keys()
                else 0.0
            )
            tax.balance_refund = (
                total_balance_refund[tax.id]
                if tax.id in total_balance_refund.keys()
                else 0.0
            )
            tax.base_balance_refund = (
                total_base_balance_refund[tax.id]
                if tax.id in total_base_balance_refund.keys()
                else 0.0
            )
            tax.balance = tax.balance_regular + tax.balance_refund
            tax.base_balance = (
                tax.base_balance_regular + tax.base_balance_refund)

    def get_target_type_list(self, move_type=None):
        if move_type == 'refund':
            return ['receivable_refund', 'payable_refund']
        elif move_type == 'regular':
            return ['receivable', 'payable', 'liquidity', 'other']
        return []

    def get_target_state_list(self, target_move="posted"):
        if target_move == 'posted':
            state = ['posted']
        elif target_move == 'all':
            state = ['posted', 'draft']
        else:
            state = []
        return state

    def get_move_line_partial_where(self, from_date, to_date, company_ids):
        query = "aml.date <= %s AND aml.date >= %s AND aml.company_id IN %s"
        params = [to_date, from_date, tuple(company_ids)]
        return query, params

    def compute_balance(self, tax_or_base="tax", move_type=None):
        # There's really bad performace in m2m fields.
        # So we better do a direct query.
        # See https://github.com/odoo/odoo/issues/30350
        _select, _group_by, query, params = self.get_move_lines_query(
            tax_or_base=tax_or_base, move_type=move_type
        )
        query = query.format(select_clause=_select, group_by_clause=_group_by)
        self.env.cr.execute(query, params)  # pylint: disable=E8103
        results = self.env.cr.fetchall()
        total_balance = {}
        for balance, tax_id in results:
            total_balance[tax_id] = balance
        return total_balance

    def get_move_lines_query(self, tax_or_base="tax", move_type=None):
        from_date, to_date, company_ids, target_move = self.get_context_values()
        state_list = self.get_target_state_list(target_move)
        type_list = self.get_target_type_list(move_type)
        base_query = self.get_move_lines_base_query()
        _where = ""
        _joins = ""
        _group_by = ""
        _params = []
        _select = "SELECT SUM(balance)"
        _group_by = " GROUP BY "
        where, params = self.get_move_line_partial_where(
            from_date, to_date, company_ids
        )
        _where += where
        _params += params
        if tax_or_base == "tax":
            select, where, group_by, params = self.get_balance_where(
                state_list, type_list
            )
            _where += where
            _params += params
            _select += select
            _group_by += group_by
        elif tax_or_base == "base":
            select, joins, where, group_by, params = self.get_base_balance_where(
                state_list, type_list
            )
            _where += where
            _joins += joins
            _params += params
            _select += select
            _group_by += group_by
        query = base_query.format(
            select_clause="{select_clause}",
            where_clause=_where,
            additional_joins=_joins,
            group_by_clause="{group_by_clause}",
        )
        return _select, _group_by, query, _params

    def get_move_lines_base_query(self):
        return (
            "{select_clause} FROM account_move_line AS aml "
            "INNER JOIN account_move AS am ON aml.move_id = am.id "
            "{additional_joins}"
            " WHERE {where_clause}"
            "{group_by_clause}"
        )

    def get_balance_where(self, state_list, type_list):
        select = ", aml.tax_line_id  as tax_id"
        where = (
            " AND am.state IN %s"
            " AND  aml.tax_line_id IS NOT NULL"
            " AND aml.tax_exigible = True"
        )
        group_by = "aml.tax_line_id"
        params = [tuple(state_list)]
        if type_list:
            where += " AND am.move_type IN %s"
            params += [tuple(type_list)]
        return select, where, group_by, params

    def get_base_balance_where(self, state_list, type_list):
        select = ", rel.account_tax_id as tax_id"
        joins = (
            " INNER JOIN account_move_line_account_tax_rel AS rel "
            "ON aml.id = rel.account_move_line_id"
        )
        group_by = "rel.account_tax_id"
        where = " AND am.state IN %s" " AND aml.tax_exigible = True "
        params = [tuple(state_list)]
        if type_list:
            where += " AND am.move_type IN %s"
            params += [tuple(type_list)]
        return select, joins, where, group_by, params

    def get_move_lines_domain(self, tax_or_base="tax", move_type=None):
        _select, _group_by, query, params = self.get_move_lines_query(
            tax_or_base=tax_or_base, move_type=move_type
        )
        _select = "SELECT aml.id"
        _group_by = ""
        if tax_or_base == "tax":
            query += " AND aml.tax_line_id = " + str(self.id)
        elif tax_or_base == "base":
            query += " AND rel.account_tax_id = " + str(self.id)
        query = query.format(select_clause=_select, group_by_clause=_group_by)
        self.env.cr.execute(query, params)  # pylint: disable=E8103
        amls = []
        for (aml_id,) in self.env.cr.fetchall():
            amls.append(aml_id)
        domain = [("id", "in", amls)]
        return domain

    def get_lines_action(self, tax_or_base='tax', move_type=None):
        domain = self.get_move_lines_domain(
            tax_or_base=tax_or_base, move_type=move_type)
        action = self.env.ref('account.action_account_moves_all_tree')
        vals = action.read()[0]
        vals['context'] = {}
        vals['domain'] = domain
        return vals

    @api.multi
    def view_tax_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base='tax')

    @api.multi
    def view_base_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base='base')

    @api.multi
    def view_tax_regular_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base='tax', move_type='regular')

    @api.multi
    def view_base_regular_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base='base', move_type='regular')

    @api.multi
    def view_tax_refund_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base='tax', move_type='refund')

    @api.multi
    def view_base_refund_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base='base', move_type='refund')
