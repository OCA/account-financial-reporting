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

Credits
=======

Contributors
------------

* Alexis de Lattre, Akretion <alexis.delattre@akretion.com>
* Luc De Meyer, Noviat <info@noviat.com>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
