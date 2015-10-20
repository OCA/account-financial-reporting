.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=============================
Intrastat reports for Belgium
=============================


This module implements the Belgian Intrastat reporting.

The report can be reviewed and corrected where needed before
the creation of the XML file for the online declaration (ONEGATE).

More information can be found on the National Bank website:
https://www.nbb.be/en/statistics/foreign-trade


Installation
============

WARNING:

This module conflicts with the module *report_intrastat* and *l10n_be_intrastat*
from the official addons.
If you have already installed these modules,
you should uninstall them before installing this module.


Configuration
=============

This module adds the following configuration parameters:

* Company

  - Arrivals : Exempt, Standard or Extended
  - Dispatches : Exempt, Standard or Extended
  - Default Intrastat Region
  - Default Intrastat Transport Mode (Extended Declaration)
  - Default Intrastat Incoterm (Extended Declaration)

* Warehouse

  - Intrastat Region to cope with warehouses in different regions

    The configuration of the Intrastat Region on a Warehouse, requires a login
    belonging to the "Belgian Intrastat Product Declaration" security group.

* Inrastat Codes, Supplementary Units, Transaction Tyoes, Transport Modes, Regions

  Cf. menu Accounting / Configuration / Miscellaneous / Intrastat Configuration

  The configuration data is loaded when installing the module.

  A configuration wizard also allows to update the Intrastat Codes so that you can easily
  synchronise your Odoo instance with the latest list of codes supplied with this module
  (an update is published on an annual basis by the Belgian National Bank).

  Some Intrastat Codes require an Intrastat Supplementary Unit.
  In this case, an extra configuration is needed to map the Intrastat Supplementary Unit
  to the corresponding Odoo Unit Of Measurement.

* Product

  You can define a default Intrastat Code on the Product or the Product Category.

Usage
=====

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/91/8.0


Known issues / Roadmap
======================

- Product movements without invoices are not included in the current version
  of this module and must be added manually to the report lines
  before generating the ONEGATE XML declaration.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-reporting/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback `here <https://github.com/OCA/
account-financial-reporting/issues/new?body=module:%20
l10n_be_report_intrastat%0Aversion:%20
8.0.0.1%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Luc De Meyer, Noviat <info@noviat.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
