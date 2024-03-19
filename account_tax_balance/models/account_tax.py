# Copyright 2016 Lorenzo Battistini - Agile Business Group
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    balance = fields.Float(string="Total Balance", compute="_compute_balance")
    base_balance = fields.Float(string="Total Base Balance", compute="_compute_balance")
    balance_regular = fields.Float(string="Balance", compute="_compute_balance")
    base_balance_regular = fields.Float(
        string="Base Balance", compute="_compute_balance"
    )
    balance_refund = fields.Float(compute="_compute_balance")
    base_balance_refund = fields.Float(compute="_compute_balance")
    has_moves = fields.Boolean(
        string="Has balance in period",
        compute="_compute_has_moves",
        search="_search_has_moves",
    )

    def get_context_values(self):
        context = self.env.context
        actual_company_id = context.get("company_id", self.env.company.id)
        return (
            context.get("from_date", fields.Date.context_today(self)),
            context.get("to_date", fields.Date.context_today(self)),
            context.get("company_ids", [actual_company_id]),
            context.get("target_move", "posted"),
        )

    def _account_tax_ids_with_moves_query(self):
        from_date, to_date, company_ids, _ = self.get_context_values()
        company_ids = tuple(company_ids)
        query = """
            SELECT id
            FROM account_tax at
            WHERE
            company_id in %s AND
            EXISTS (
              SELECT 1 FROM account_move_Line aml
              WHERE
                date >= %s AND
                date <= %s AND
                company_id in %s AND (
                  tax_line_id = at.id OR
                  EXISTS (
                    SELECT 1 FROM account_move_line_account_tax_rel
                    WHERE account_move_line_id = aml.id AND
                      account_tax_id = at.id
                  )
                )
            )
        """
        params = (company_ids, from_date, to_date, company_ids)
        return query, params

    def _account_tax_ids_with_moves(self):
        """Return all account.tax ids for which there is at least
        one account.move.line in the context period
        for the user company.

        Caveat: this ignores record rules and ACL but it is good
        enough for filtering taxes with activity during the period.
        """
        query, params = self._account_tax_ids_with_moves_query()
        self.env.cr.execute(query, params)
        return [r[0] for r in self.env.cr.fetchall()]

    def _compute_has_moves(self):
        ids_with_moves = set(self._account_tax_ids_with_moves())
        for tax in self:
            tax.has_moves = tax.id in ids_with_moves

    @api.model
    def _is_unsupported_search_operator(self, operator):
        return operator != "="

    @api.model
    def _search_has_moves(self, operator, value):
        if self._is_unsupported_search_operator(operator) or not value:
            raise ValueError(_("Unsupported search operator"))
        ids_with_moves = self._account_tax_ids_with_moves()
        return [("id", "in", ids_with_moves)]

    @api.depends_context(
        "from_date",
        "to_date",
        "company_ids",
        "target_move",
    )
    def _compute_balance(self):
        for tax in self:
            tax.balance_regular = tax.compute_balance(
                tax_or_base="tax", financial_type="regular"
            )
            tax.base_balance_regular = tax.compute_balance(
                tax_or_base="base", financial_type="regular"
            )
            tax.balance_refund = tax.compute_balance(
                tax_or_base="tax", financial_type="refund"
            )
            tax.base_balance_refund = tax.compute_balance(
                tax_or_base="base", financial_type="refund"
            )
            tax.balance = tax.balance_regular + tax.balance_refund
            tax.base_balance = tax.base_balance_regular + tax.base_balance_refund

    def get_target_type_list(self, financial_type=None):
        if financial_type == "refund":
            return ["receivable_refund", "payable_refund"]
        elif financial_type == "regular":
            return ["receivable", "payable", "liquidity", "other"]
        return []

    def get_target_state_list(self, target_move="posted"):
        if target_move == "posted":
            state = ["posted"]
        elif target_move == "all":
            state = ["posted", "draft"]
        else:
            state = []
        return state

    def get_move_line_partial_domain(self, from_date, to_date, company_ids):
        return [
            ("date", "<=", to_date),
            ("date", ">=", from_date),
            ("company_id", "in", company_ids),
        ]

    def compute_balance(self, tax_or_base="tax", financial_type=None):
        self.ensure_one()
        domain = self.get_move_lines_domain(
            tax_or_base=tax_or_base, financial_type=financial_type
        )
        # balance is debit - credit whereas on tax return you want to see what
        # vat has to be paid so:
        # VAT on sales (credit) - VAT on purchases (debit).

        balance = self.env["account.move.line"].read_group(domain, ["balance"], [])[0][
            "balance"
        ]
        return balance and -balance or 0

    def get_balance_domain(self, state_list, type_list):
        domain = [
            ("move_id.state", "in", state_list),
            ("tax_line_id", "=", self.id),
        ]
        domain.extend(self.env["account.move.line"]._get_tax_exigible_domain())
        if type_list:
            domain.append(("move_id.financial_type", "in", type_list))
        return domain

    def get_base_balance_domain(self, state_list, type_list):
        domain = [
            ("move_id.state", "in", state_list),
            ("tax_ids", "in", self.id),
        ]
        domain.extend(self.env["account.move.line"]._get_tax_exigible_domain())
        if type_list:
            domain.append(("move_id.financial_type", "in", type_list))
        return domain

    def get_move_lines_domain(self, tax_or_base="tax", financial_type=None):
        from_date, to_date, company_ids, target_move = self.get_context_values()
        state_list = self.get_target_state_list(target_move)
        type_list = self.get_target_type_list(financial_type)
        domain = self.get_move_line_partial_domain(from_date, to_date, company_ids)
        balance_domain = []
        if tax_or_base == "tax":
            balance_domain = self.get_balance_domain(state_list, type_list)
        elif tax_or_base == "base":
            balance_domain = self.get_base_balance_domain(state_list, type_list)
        domain.extend(balance_domain)
        return domain

    def get_lines_action(self, tax_or_base="tax", financial_type=None):
        domain = self.get_move_lines_domain(
            tax_or_base=tax_or_base, financial_type=financial_type
        )
        action = self.env.ref("account.action_account_moves_all_tree")
        vals = action.sudo().read()[0]
        vals["context"] = {}
        vals["domain"] = domain
        return vals

    def view_tax_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base="tax")

    def view_base_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base="base")

    def view_tax_regular_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base="tax", financial_type="regular")

    def view_base_regular_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base="base", financial_type="regular")

    def view_tax_refund_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base="tax", financial_type="refund")

    def view_base_refund_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base="base", financial_type="refund")
