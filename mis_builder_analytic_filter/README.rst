.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===========================
MIS Builder Analytic Filter
===========================

This module extends the functionality of mis_builder to
provide filtering on analytic axis.

Installation
============

There is no specific installation procedure for this module.

Configuration and Usage
=======================

In Accounting > Reporting > MIS Reports, there is a new field
'Analytic Account' which can be used to filter move lines on an
analytic axis.

This filter is also available on the MIS Report widget, so the user
can change the filter in the preview and dashboard views.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/91/10.0

Known issues / Roadmap
======================

* While useful as is, we are aware that such analytic filtering may need
  to be customized heavily depending on the customer context. This module can
  be extended or considered as an example.

* At the moment, no filtering is done on other queries than move lines.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-reporting/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Adrien Peiffer <adrien.peiffer@acsone.eu>
* Stéphane Bidoul <stephane.bidoul@acsone.eu>

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
