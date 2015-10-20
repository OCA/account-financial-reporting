.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3


============================================
Harmonized System Codes (and National Codes)
============================================

This module contains the objects for Harmonised System Codes (H.S. codes). The full nomenclature is available from the `World Customs Organisation <http://www.wcoomd.org/>`. These code are usually required on the Proforma invoices that are attached to the packages that are shipped abroad.

This module also handle the local/national extensions to the H.S. codes. The import of the full nomenclature is not provided by this module ; it should be provided by localization modules.

You will also be able to configure the country of origin of a product, which is often required on the proforma invoice for the customs.

This module should be usefull for all companies that export physical goods abroad. This module is also used by the Intrastat modules for the European Union, cf the *intrastat_product* module.


Installation
============

This module is NOT compatible with the *report_intrastat* module from the official addons.


Usage
=====

To create H.S. codes, go to the menu *Sales > Configuration > Product Categories and Attributes > H.S. Codes*.

Then you will be able to set the H.S. code on an product (under the *Information* tab) or on a product category. On the product form, you will also be able to set the *Country of Origin* of a product (for example, if the product is *made in China*, select *China* as *Country of Origin*).

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/91/8.0


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-reporting/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback `here <https://github.com/OCA/
account-financial-reporting/issues/new?body=module:%20
product_harmonized_system%0Aversion:%20
8.0.0.2%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


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

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
