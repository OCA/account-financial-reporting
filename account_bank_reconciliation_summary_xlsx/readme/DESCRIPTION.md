# Bank Reconciliation Report (XLSX)

This module adds a Bank Reconciliation Report in Odoo in XLSX format.

For each bank journal, the report displays:

- The balance of the bank account in the accounting
- The list of journal items of the bank account not linked to any bank statement lines
- The list of draft bank statement lines not linked to any journal items
- The computed balance of the bank account at the bank

The last field (computed balance of the bank account at the bank) must be compared to the real bank account balance at the bank. If there is a difference, you need to find the error in the accounting.

The field **Computed balance of the bank account at the bank** is a formula, so you can easily change its computation to try to find the difference with the real bank account balance at the bank.

## Date Selection Options

A **Bank Journal** field is available in the wizard. The report will be generated for the selected bank journal.

An **End Date** field and a **Date Range** (`date_range_id`) field are added in the wizard.

Users can generate the Bank Reconciliation Report using the following options:

- **Using Date Range**
  - Select a Date Range, which automatically sets the From Date and To Date
  - The report is generated based on the selected range

- **Using Manual Dates**
  - Users can define both From Date and End Date, or
  - If only the End Date is provided, the report is generated from the beginning up to the selected end date

## Configuration

To use the Date Range feature, configure it from:

**Accounting → Configuration → Date Ranges → Date Ranges**

Users must create:
- A **Date Range Type**
- Corresponding **Date Ranges**

These will then be available in the wizard.
