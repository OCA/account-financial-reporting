.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==============
Intrastat Base
==============

This module contains common functions for the intrastat reporting and
should be used in combination with the generic reporting module
*intrastat_product* and with the country-specific reporting modules such
as:

- *l10n_fr_intrastat_service*:
  the module for the *Déclaration Européenne des Services* (DES) for France
- *l10n_fr_intrastat_product*:
  the module for the *Déclaration d'Echange de Biens* (DEB) for France
- *l10n_be_intrastat_product*:
  the module for the Intrastat Declaration for Belgium.


Installation
============

WARNING:

This module conflicts with the module *report_intrastat* from the official addons.
If you have already installed the module *report_intrastat*,
you should uninstall it first before installing this module.

Usage
=====

This module adds an intrastat property on countries and activates this property
on the 28 countries of the European Union.

With this module, the country field on partners becomes a required field.

It adds an option *Exclude invoice line from intrastat if this tax is present*
on taxes.

It adds a tab *Intrastat* on the company form view.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/91/8.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-reporting/issues>`_. In case
of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and
welcomed feedback.

Credits
=======

Contributors
------------

* Alexis de Lattre, Akretion <alexis.delattre@akretion.com>
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

To contribute to this module, please visit https://odoo-community.org.
