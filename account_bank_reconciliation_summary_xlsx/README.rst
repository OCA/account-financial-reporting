.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===============================
Bank Reconciliation Report XLSX
===============================

This module adds a Bank Reconciliation Report in Odoo in XLSX format. For each bank journal, the report displays:

1. The balance of the bank account in the accounting,
2. The list of journal items of the bank account not linked to any bank statement lines,
3. The list of draft bank statement lines not linked to any journal items,
4. The computed balance of the bank account at the bank.

The last field (computed balance of the bank account at the bank) must be compared to the real bank account balance at the bank. If there is a difference, you need to find the error in the accounting. The field *Computed balance of the bank account at the bank* is a formula, so you can easily change its computation to try to find the difference with the real bank account balance at the bank.

Configuration
=============

This module doesn't require any configuration.

Usage
=====

You can launch the Bank Reconciliation Report wizard from:

* the menu *Accounting > Reports > OCA accounting reports > Bank Reconciliation*,
* the form view of a bank statement: click on the button *Bank Reconciliation Report*.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/91/10.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-reporting/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Alexis de Lattre <alexis.delattre@akretion.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
