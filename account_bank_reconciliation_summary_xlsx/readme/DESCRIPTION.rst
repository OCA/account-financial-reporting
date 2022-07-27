This module adds a Bank Reconciliation Report in Odoo in XLSX format. For each bank journal, the report displays:

1. The balance of the bank account in the accounting,
2. The list of journal items of the bank account not linked to any bank statement lines,
3. The list of draft bank statement lines not linked to any journal items,
4. The computed balance of the bank account at the bank.

The last field (computed balance of the bank account at the bank) must be compared to the real bank account balance at the bank. If there is a difference, you need to find the error in the accounting. The field *Computed balance of the bank account at the bank* is a formula, so you can easily change its computation to try to find the difference with the real bank account balance at the bank.
