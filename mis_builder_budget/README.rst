.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==================
Mis Builder Budget
==================

Create budgets for MIS reports.

This module lets you create budgets for any MIS report. Several budgets
can be created for a given report template (ie one budget per year). Budget
figures are provided at the KPI level, with different time periods. A budget
can then be selected as a data source for a MIS report column, and the report
will show the budgeted values for each KPI, adjusted for the period of the 
column.

Usage
=====

To use this module, you first need to flag at least some KPI in a MIS
report to be budgetable. You also need to configure the accumulation method
on the KPI according to their type. 

The accumulation method determines how budgeted values spanning over a
time period are transformed to match the reporting period.

* Sum: values of shorter period are added, values of longest or partially overlapping 
  periods are adjusted pro-rata temporis (eg monetary amount such as revenue).
* Average: values of included period are averaged with a pro-rata temporis weight.
  Typically used for values that do not accumulate over type (eg a number of employees).

When KPI are configured, you need to create a budget, then click on the budget items
button to create or import the budgeted amounts for all your KPI and time periods.

Finally, a column (aka period) must be added to a MIS report instance, selecting your
newly created budget as a data source. The data will be adjusted to the reporting period
when displayed. Columns can be compared by adding a column of type "comparison" or "sum".

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/91/10.0

Known issues / Roadmap
======================

* Improve the workflow (eg, make non-draft budgets readonly).

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/{project_repo}/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Author
------

* Stéphane Bidoul <stephane.bidoul@acsone.eu>

Contributors
------------

* Adrien Peiffer <adrien.peiffer@acsone.eu>
* Benjamin Willing <benjamine.willig@acsone.eu>

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
