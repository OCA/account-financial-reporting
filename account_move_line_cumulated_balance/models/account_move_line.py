# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools import SQL


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    cumulated_balance = fields.Monetary(group_operator="max")

    def _read_group_select(self, aggregate_spec, query):
        if aggregate_spec == "cumulated_balance:max":
            return SQL("MAX(%s)", SQL.identifier(query.table, "balance")), ["balance"]
        return super()._read_group_select(aggregate_spec, query)

    @api.model
    def read_group(
        self,
        domain,
        fields,
        groupby,
        offset=0,
        limit=None,
        orderby=False,
        lazy=True,
    ):
        fields = list(fields or [])
        with_cumulated_balance = any(
            self._read_group_field_is_cumulated_balance(field) for field in fields
        )
        if with_cumulated_balance:
            fields = [
                field
                for field in fields
                if not self._read_group_field_is_cumulated_balance(field)
            ]
        groups = super().read_group(
            domain,
            fields,
            groupby,
            offset=offset,
            limit=limit,
            orderby=orderby,
            lazy=lazy,
        )
        if with_cumulated_balance:
            self._read_group_set_cumulated_balance(groups, groupby)
        return groups

    @api.model
    def _read_group_field_is_cumulated_balance(self, field):
        return field == "cumulated_balance" or field.startswith("cumulated_balance:")

    @api.model
    def _read_group_set_cumulated_balance(self, groups, groupby):
        order = self.env.context.get("order_cumulated_balance") or self._order
        groupby = [groupby] if isinstance(groupby, str) else groupby
        for group in groups:
            group_domain = group.get("__domain")
            if not group_domain:
                group["cumulated_balance"] = False
                continue
            first_line = self.search(group_domain, limit=1, order=order)
            group_domain = self._cumulated_balance_to_tuple(group_domain)
            group["cumulated_balance"] = first_line.with_context(
                account_move_line_cumulated_balance_guard=self.env.context.get(
                    "account_move_line_cumulated_balance_guard"
                ),
                domain_cumulated_balance=group_domain,
                group_by=groupby,
                order_cumulated_balance=order,
            ).cumulated_balance

    @api.model
    def _cumulated_balance_to_tuple(self, value):
        if isinstance(value, list | tuple):
            return tuple(self._cumulated_balance_to_tuple(item) for item in value)
        return value

    @api.model
    def _cumulated_balance_grouped_by_account(self):
        return any(
            groupby.split(":", 1)[0] == "account_id"
            for groupby in self._cumulated_balance_context_groupby()
        )

    @api.model
    def _cumulated_balance_filtered_by_account(self):
        domain = self.env.context.get("domain_cumulated_balance") or ()
        return self._domain_has_account_filter(domain)

    @api.model
    def _domain_has_account_filter(self, domain):
        for item in domain:
            if not isinstance(item, list | tuple):
                continue
            if item and item[0] == "account_id":
                return True
            if self._domain_has_account_filter(item):
                return True
        return False

    @api.depends_context(
        "account_move_line_cumulated_balance_guard",
        "domain_cumulated_balance",
        "group_by",
        "order_cumulated_balance",
    )
    def _compute_cumulated_balance(self):
        if (
            self.env.context.get("account_move_line_cumulated_balance_guard")
            and not self._cumulated_balance_grouped_by_account()
            and not self._cumulated_balance_filtered_by_account()
        ):
            self.cumulated_balance = 0
            return
        if self.env.context.get("account_move_line_cumulated_balance_guard"):
            return self._compute_cumulated_balance_with_initial_balance()
        return super()._compute_cumulated_balance()

    def _compute_cumulated_balance_with_initial_balance(self):
        self._compute_cumulated_balance_partitioned_by_groupby_fields()
        domain = list(self.env.context.get("domain_cumulated_balance") or [])
        initial_date_domain = self._cumulated_balance_initial_date_domain(domain)
        if not initial_date_domain:
            return
        initial_balances = self._get_cumulated_balance_initial_balances(
            domain, initial_date_domain
        )
        for line in self:
            line.cumulated_balance += initial_balances.get(
                self._cumulated_balance_initial_group_key_from_record(line), 0
            )

    def _compute_cumulated_balance_partitioned_by_groupby_fields(self):
        order = self.env.context.get("order_cumulated_balance")
        if not order:
            self.cumulated_balance = 0
            return
        domain = list(self.env.context.get("domain_cumulated_balance") or [])
        query = self._where_calc(domain)
        sql_order = self._order_to_sql(
            order,
            query,
            reverse=self._cumulated_balance_order_needs_reverse(order),
        )
        sql_partition = SQL(", ").join(
            SQL.identifier(query.table, field_name)
            for field_name in self._cumulated_balance_initial_groupby_fields()
        )
        self.env.cr.execute(
            query.select(
                SQL.identifier(query.table, "id"),
                SQL(
                    "SUM(%s) OVER ("
                    "PARTITION BY %s "
                    "ORDER BY %s "
                    "ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW"
                    ")",
                    SQL.identifier(query.table, "balance"),
                    sql_partition,
                    sql_order,
                ),
            )
        )
        result = dict(self.env.cr.fetchall())
        for line in self:
            line.cumulated_balance = result[line.id]

    @api.model
    def _cumulated_balance_order_needs_reverse(self, order):
        for order_item in order.split(","):
            order_parts = order_item.strip().lower().split()
            if not order_parts:
                continue
            if order_parts[0] == "date":
                return "desc" in order_parts
        return True

    @api.model
    def _cumulated_balance_initial_date_domain(self, domain):
        initial_bound = self._cumulated_balance_initial_bound(domain)
        if not initial_bound:
            return []
        date_from, include_date = initial_bound
        if include_date:
            return [("date", "<=", date_from)]
        return [("date", "<", date_from)]

    @api.model
    def _cumulated_balance_initial_bound(self, domain):
        if not domain:
            return None
        initial_bound, _index = self._initial_bound_from_normalized_domain(
            expression.normalize_domain(domain), 0
        )
        return initial_bound

    @api.model
    def _initial_bound_from_normalized_domain(self, domain, index):
        token = domain[index]
        if expression.is_leaf(token):
            return self._initial_bound_from_leaf(token), index + 1
        if token == expression.NOT_OPERATOR:
            return None, self._initial_bound_from_normalized_domain(domain, index + 1)[
                1
            ]
        left, index = self._initial_bound_from_normalized_domain(domain, index + 1)
        right, index = self._initial_bound_from_normalized_domain(domain, index)
        if token == expression.AND_OPERATOR:
            return self._combine_initial_bounds_and(left, right), index
        return self._combine_initial_bounds_or(left, right), index

    @api.model
    def _initial_bound_from_leaf(self, leaf):
        if leaf[0] != "date" or leaf[1] not in (">", ">=", "=") or not leaf[2]:
            return None
        return fields.Date.to_date(leaf[2]), leaf[1] == ">"

    @api.model
    def _combine_initial_bounds_and(self, left, right):
        if not left or not right:
            return left or right
        if left[0] != right[0]:
            return max(left, right, key=lambda item: item[0])
        return left[0], left[1] or right[1]

    @api.model
    def _combine_initial_bounds_or(self, left, right):
        if not left or not right:
            return None
        if left[0] != right[0]:
            return min(left, right, key=lambda item: item[0])
        return left[0], left[1] and right[1]

    def _get_cumulated_balance_initial_balances(self, domain, initial_date_domain):
        accounts = self.account_id
        if not accounts:
            return {}
        base_domain = self._cumulated_balance_domain_without_date(domain)
        groupby_fields = self._cumulated_balance_initial_groupby_fields()
        initial_balances = {}
        for company in self.company_id:
            fy_start_date = company.compute_fiscalyear_dates(initial_date_domain[0][2])[
                "date_from"
            ]
            company_domain = expression.AND(
                [
                    base_domain,
                    initial_date_domain,
                    [("company_id", "=", company.id)],
                    [("account_id", "in", accounts.ids)],
                    [
                        "|",
                        ("account_id.include_initial_balance", "=", True),
                        "&",
                        ("account_id.include_initial_balance", "=", False),
                        ("date", ">=", fy_start_date),
                    ],
                ]
            )
            groups = self.read_group(
                company_domain,
                ["balance:sum"],
                groupby_fields,
                lazy=False,
            )
            for group in groups:
                initial_balances[
                    self._cumulated_balance_initial_group_key_from_group(
                        group, groupby_fields
                    )
                ] = group["balance"]
        return initial_balances

    @api.model
    def _cumulated_balance_initial_groupby_fields(self):
        groupby_fields = ["account_id", "company_id"]
        for groupby in self._cumulated_balance_context_groupby():
            field_name = groupby.split(":", 1)[0]
            field = self._fields.get(field_name)
            if (
                not field
                or not field.store
                or not getattr(field, "column_type", None)
                or field_name in groupby_fields
                or field.type in {"date", "datetime"}
            ):
                continue
            groupby_fields.append(field_name)
        return groupby_fields

    @api.model
    def _cumulated_balance_context_groupby(self):
        group_by = self.env.context.get("group_by") or ()
        if isinstance(group_by, str):
            return [groupby.strip() for groupby in group_by.split(",") if groupby]
        return group_by

    @api.model
    def _cumulated_balance_initial_group_key_from_record(self, record):
        return tuple(
            self._cumulated_balance_initial_group_value_from_record(record, field_name)
            for field_name in self._cumulated_balance_initial_groupby_fields()
        )

    @api.model
    def _cumulated_balance_initial_group_value_from_record(self, record, field_name):
        value = record[field_name]
        field = self._fields[field_name]
        if field.type == "many2one":
            return value.id or False
        return value

    @api.model
    def _cumulated_balance_initial_group_key_from_group(self, group, groupby_fields):
        return tuple(
            self._cumulated_balance_initial_group_value_from_group(group, field_name)
            for field_name in groupby_fields
        )

    @api.model
    def _cumulated_balance_initial_group_value_from_group(self, group, field_name):
        value = group[field_name]
        field = self._fields[field_name]
        if field.type == "many2one":
            return value and value[0]
        return value

    @api.model
    def _cumulated_balance_domain_without_date(self, domain):
        normalized_domain = expression.normalize_domain(domain)
        domain_without_date, _index = self._remove_date_leaves(normalized_domain, 0)
        return domain_without_date or []

    @api.model
    def _remove_date_leaves(self, domain, index):
        token = domain[index]
        if expression.is_leaf(token):
            return (None if token[0] == "date" else [token]), index + 1
        if token == expression.NOT_OPERATOR:
            child, index = self._remove_date_leaves(domain, index + 1)
            return ([token] + child if child else None), index
        left, index = self._remove_date_leaves(domain, index + 1)
        right, index = self._remove_date_leaves(domain, index)
        if token == expression.AND_OPERATOR:
            return self._combine_domain_operator(token, left, right), index
        if not left or not right:
            return None, index
        return [token] + left + right, index

    @api.model
    def _combine_domain_operator(self, operator, left, right):
        if left and right:
            return [operator] + left + right
        return left or right

    @api.model
    def _domain_leaves(self, domain):
        for token in expression.normalize_domain(domain):
            if expression.is_leaf(token):
                yield token
