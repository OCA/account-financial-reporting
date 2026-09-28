This module extends the four OCA financial reports — **General Ledger**,
**Journal Ledger**, **Open Items**, and **Aged Partner Balance** — with
an optional **Analytic Tags** column.

When the *Show Analytic Tags* checkbox is enabled in the report wizard,
every journal item row shows the analytic tags attached to that move
line, placed immediately after the *Analytic Distribution* column. The
extra column is rendered in both the PDF and XLSX outputs.

For the Aged Partner Balance report the column only appears when *Show
Move Line Details* is also active, because analytic tags are a property
of individual journal items, not of partner-level aggregates.
