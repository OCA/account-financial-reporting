This module adds a dedicated journal items list to use Odoo's native cumulated
balance.

The value is computed by `account.move.line` from the current list domain and sort
order, so it behaves like a running balance for the records displayed in the
view.

To avoid expensive accidental computations, the dedicated action only computes
the cumulated balance when the list is grouped or filtered by account.

When the list has a lower date filter, the cumulated balance includes the
initial balance before that date for each account, while keeping the visible
lines restricted to the selected period.

If the list is grouped by additional stored fields, such as partner, the visible
cumulated balance and the initial balance are computed independently for each
group.
