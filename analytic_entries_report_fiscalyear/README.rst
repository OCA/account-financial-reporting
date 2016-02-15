.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

=====================================================
Analytic Entries Statistics per fiscal period or year
=====================================================

Standard statistics over analytic entries don't allow grouping per fiscal year
or period. This is partly because this concept doesn't fit analytic entries
completely, as they don't necessarily are connected to a fiscal period.

This addon overrides the standard analytic entries statistics to figure out the
fiscal period based on the linked move line and falls back to the date if
there's none.

Usage
=====

After installation of this module, you'll find filters for the fiscal year and
period.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
    :alt: Try me on Runbot
    :target: https://runbot.odoo-community.org/runbot/91/8.0

For further information, please visit:

* https://www.odoo.com/forum/help-1

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/analytic_entries_report_fiscalyear/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/analytic_entries_report_fiscalyear/issues/new?body=module:%20analytic_entries_report_fiscalyear%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------

* Holger Brunn <hbrunn@therp.nl>

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
