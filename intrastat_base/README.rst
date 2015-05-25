.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

Intrastat Base Module
=====================

This module contains common functions for the Intrastat reporting and
should be used in combination with country specific reporting modules
such as

- l10n_fr_intrastat_service:
  the module for the "Déclaration Européenne des Services" (DES)
- l10n_fr_intrastat_product:
  the module for the "Déclaration d'Echange de Biens" (DEB)

Installation
============

WARNING:
This module conflicts with the module "report_intrastat" from the addons.
If you have already installed the module "report_intrastat",
you should uninstall it first before installing this module.

Credits
=======

Author
------
* Alexis de Lattre, Akretion <alexis.delattre@akretion.com>
