.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

====================================
Print Partner Outstanding Statement
====================================

The outstanding statement provides details of all outstanding partner receivables or payables
up to a particular date. This includes all unpaid invoices, unclaimed refunds and
outstanding payments. The list is displayed in chronological order and is split by currencies.

Aging details can be shown in the report, expressed in aging buckets (30 days
due, ...), so the customer or vendor can review how much is open, due or overdue.

Configuration
=============

Users willing to access to this report should have proper Accounting & Finance rights:

#. Go to *Settings / Users* and edit your user to add the corresponding access rights as follows.
#. In *Application / Accounting & Finance*, select *Billing* or *Billing Manager*
#. In *Technical Settings* mark *Show Full Accounting Features* options.

Usage
=====

To use this module, you need to:

#. Go to Invoicing > Sales > Master Data > Customers or or Invoicing > Purchases > Master Data > Vendors and select one or more
#. Press 'Action > Partner Outstanding Statement'
#. Indicate if you want to display receivables or payables, and if you want to display aging buckets


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/91/11.0

Roadmap
=======

* In v12, the module should be renamed to `Partner Outstanding Statement`.
  Maybe merge this module with the `Partner Activity Statement` module.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-reporting/issues>`_. In case of trouble,
please check there if your issue has already been reported. If you spotted it
first, help us smash it by providing detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.png>`_.

Contributors
------------

* Miquel Raïch <miquel.raich@eficent.com>

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
