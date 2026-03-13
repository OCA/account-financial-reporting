After installation, the module works automatically via a scheduled action that
generates cash basis journal items from posted entries and reconciliations.

You can view the generated cash basis journal items from the menu
**Invoicing > Reporting > Cash Basis Journal Items**.

**Integration with MIS Builder:**

The ``cash.basis.move.line`` model can be used as a move lines data source in
the **mis-builder** module. This allows you to build MIS reports (e.g. profit
& loss, budget vs actual) on a cash basis instead of the default accrual basis.
To do so, configure your MIS report instance to use ``cash.basis.move.line``
as the move line source.
