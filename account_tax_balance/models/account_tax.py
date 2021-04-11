# © 2016 Lorenzo Battistini - Agile Business Group
# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


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
    has_moves = fields.Boolean(
        string="Has balance in period",
        compute="_compute_has_moves",
        search="_search_has_moves",
    )

    def get_context_values(self):
        context = self.env.context
        return (
            context.get('from_date', fields.Date.context_today(self)),
            context.get('to_date', fields.Date.context_today(self)),
            context.get('company_id', self.env.user.company_id.id),
            context.get('target_move', 'posted'),
        )

    def _account_tax_ids_with_moves(self):
        """ Return all account.tax ids for which there is at least
        one account.move.line in the context period
        for the user company.

        Caveat: this ignores record rules and ACL but it is good
        enough for filtering taxes with activity during the period.
        """
        req = """
            SELECT id
            FROM account_tax at
            WHERE
            company_id = %s AND
            EXISTS (
              SELECT 1 FROM account_move_Line aml
              WHERE
                date >= %s AND
                date <= %s AND
                company_id = %s AND (
                  tax_line_id = at.id OR
                  EXISTS (
                    SELECT 1 FROM account_move_line_account_tax_rel
                    WHERE account_move_line_id = aml.id AND
                      account_tax_id = at.id
                  )
                )
            )
        """
        from_date, to_date, company_id, target_move = self.get_context_values()
        self.env.cr.execute(
            req, (company_id, from_date, to_date, company_id))
        return [r[0] for r in self.env.cr.fetchall()]

    @api.multi
    def _compute_has_moves(self):
        ids_with_moves = set(self._account_tax_ids_with_moves())
        for tax in self:
            tax.has_moves = tax.id in ids_with_moves

    @api.model
    def _is_unsupported_search_operator(self, operator):
        return operator != '='

    @api.model
    def _search_has_moves(self, operator, value):
        if self._is_unsupported_search_operator(operator) or not value:
            raise ValueError(_("Unsupported search operator"))
        ids_with_moves = self._account_tax_ids_with_moves()
        return [('id', 'in', ids_with_moves)]

    def _compute_balance(self):
        for tax in self:
            tax.balance_regular = tax.compute_balance(
                tax_or_base='tax', move_type='regular')
            tax.base_balance_regular = tax.compute_balance(
                tax_or_base='base', move_type='regular')
            tax.balance_refund = tax.compute_balance(
                tax_or_base='tax', move_type='refund')
            tax.base_balance_refund = tax.compute_balance(
                tax_or_base='base', move_type='refund')
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
        self.ensure_one()
        query, params = self.get_move_lines_query(
            tax_or_base=tax_or_base, move_type=move_type
        )
        _select = "sum(aml.balance)"
        query = query.format(select_clause=_select)
        self.env.cr.execute(query, params)  # pylint: disable=E8103
        res = self.env.cr.fetchone()
        balance = 0.0
        if res:
            balance = res[0]
        return balance and -balance or 0.0

    def get_move_lines_query(self, tax_or_base="tax", move_type=None):
        from_date, to_date, company_ids, target_move = self.get_context_values()
        state_list = self.get_target_state_list(target_move)
        type_list = self.get_target_type_list(move_type)
        base_query = self.get_move_lines_base_query()
        _where = ""
        _joins = ""
        _params = []
        where, params = self.get_move_line_partial_where(
            from_date, to_date, company_ids
        )
        _where += where
        _params += params
        if tax_or_base == "tax":
            where, params = self.get_balance_where(state_list, type_list)
            _where += where
            _params += params
        elif tax_or_base == "base":
            joins, where, params = self.get_base_balance_where(state_list, type_list)
            _where += where
            _joins += joins
            _params += params
        query = base_query.format(
            select_clause="{select_clause}",
            where_clause=_where,
            additional_joins=_joins,
        )
        return query, _params

    def get_move_lines_base_query(self):
        return (
            "SELECT {select_clause} FROM account_move_line AS aml "
            "INNER JOIN account_move AS am ON aml.move_id = am.id "
            "{additional_joins}"
            " WHERE {where_clause}"
        )

    def get_balance_where(self, state_list, type_list):
        where = (
            " AND am.state IN %s AND "
            "aml.tax_line_id = %s AND "
            "aml.tax_exigible = True"
        )
        params = [tuple(state_list), self.id]
        if type_list:
            where += " AND am.move_type IN %s"
            params += [tuple(type_list)]
        return where, params

    def get_base_balance_where(self, state_list, type_list):
        joins = (
            " INNER JOIN account_move_line_account_tax_rel AS rel "
            "ON aml.id = rel.account_move_line_id"
            " INNER JOIN account_tax as tax "
            "ON tax.id = rel.account_tax_id"
        )

        where = " AND am.state IN %s" " AND tax.id = %s" " AND aml.tax_exigible = True "
        params = [tuple(state_list), self.id]
        if type_list:
            where += " AND am.move_type IN %s"
            params += [tuple(type_list)]
        return joins, where, params

    def get_move_lines_domain(self, tax_or_base="tax", move_type=None):
        query, params = self.get_move_lines_query(
            tax_or_base=tax_or_base, move_type=move_type
        )
        _select = "aml.id"
        query = query.format(select_clause=_select)
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
