.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

========================
Intrastat Product Module
========================

This module contains common objects and fields for the Intrastat Product reporting, such as the *H.S. codes* (if you are not familiar with H.S. codes, read `Wikipedia <http://en.wikipedia.org/wiki/Harmonized_System>`) and the *country of origin* on the products.

It should be used in combination with country-specific Intrastat Product reporting modules
such as:

- *l10n_fr_intrastat_product*:
  the module for the *Déclaration d'Echange de Biens* (DEB) for France
- *l10n_be_intrastat_product*:
  the module for the Intrastat Product Declaration for Belgium

These country-specific modules can be found in the OCA localization for those countries.

Installation
============

WARNING:

This module conflicts with the module *report_intrastat* from the official addons.
If you have already installed the module *report_intrastat*,
you should uninstall it before installing this module.


Usage
=====

This module is used in combination with the country-specific
localization module(s).

Coding guidelines for localization module:
------------------------------------------

We recommend to start by copying an existing module, e.g. l10n_be_intrastat_product
and adapt the code for the specific needs of your country.

* Declaration Object

  Create a new class as follows:

  .. code-block:: python

     class L10nCcIntrastatProductDeclaration(models.Model):
         _name = 'l10n.cc.intrastat.product.declaration'
         _description = "Intrastat Product Declaration for YourCountry"
         _inherit = ['intrastat.product.declaration', 'mail.thread']

  whereby cc = your country code

* Computation & Declaration Lines

  Create also new objects inheriting from the Computation and Declaration Line Objects
  so that you can add methods or customise the methods from the base modules (make a PR when
  the customization or new method is required for multiple countries).
  
  Adapt also the parent_id fields of the newly created objects
  (cf. l10n_be_intrastat_product as example).

* XML Files: Menu, Action, Views

  Cf. l10n_be_istrastat_product as example, replace "be" by your Country Code.


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/91/8.0


Known issues / Roadmap
======================

Work is in progress to migrate the existing l10n_fr_intrastat_product module
to this new reporting framework, cf. Alexis de Lattre, Akretion <alexis.delattre@akretion.com>.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-reporting/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback `here <https://github.com/OCA/
account-financial-reporting/issues/new?body=module:%20
intrastat_product%0Aversion:%20
8.0.1.4%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


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

To contribute to this module, please visit http://odoo-community.org.
