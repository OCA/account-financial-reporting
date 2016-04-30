Changelog
---------

.. Future (?)
.. ~~~~~~~~~~
.. 
.. * 

9.0.1.0.0 (2016-??-??)
~~~~~~~~~~~~~~~~~~~~~~

Most of the work for this release has been done at the Sorrento sprint
April 26-29, 2016.

* [IMP] there is now an auto-expand feature to automatically display
  a by account detail for some kpis
* [IMP] the kpi and period lists are now manipulated through forms instead
  of directly in the tree views, this improves usability
* [IMP] it is now possible to create a report through a wizard, such
  reports are deemed temporary and available through a "Last Reports Generated"
  menu, they are garbaged collected automatically, unless saved permanently,
  which can be done using a Save button
* [IMP] there is now a beginner mode to configure simple reports with
  only one period
* [IMP] it is now easier to configure periods with fixed start/end dates
* [IMP] the new sub-kpi mechanism allows the creation of columns
  with multiple values, or columns with different values
* [IMP] thanks to the new style model, the Excel export is now styled
* [IMP] a new style model is now used to centralize style configuration
* [FIX] use =like instead of like to search for accounts, because
  the % are added by the user in the expressions
* [FIX] Correctly compute the initial balance of income and expense account
  based on the start of the fiscal year 
* [IMP] Support date ranges (from OCA/server-tools/date_range) as a more
  flexible alternative to fiscal periods
* v9 migration: fiscal periods are removed, account charts are removed,
  consolidation accounts have been removed

8.0.1.0.0 (2016-04-27)
~~~~~~~~~~~~~~~~~~~~~~

* The copy of a MIS Report Instance now copies period.
  https://github.com/OCA/account-financial-reporting/pull/181
* The copy of a MIS Report Template now copies KPIs and queries.
  https://github.com/OCA/account-financial-reporting/pull/177
* Usability: the default view for MIS Report instances is now the rendered preview,
  and the settings are accessible through a gear icon in the list view and
  a button in the preview.
  https://github.com/OCA/account-financial-reporting/pull/170
* Display blank cells instead of 0.0 when there is no data.
  https://github.com/OCA/account-financial-reporting/pull/169
* Usability: better layout of the MIS Report periods settings on small screens.
  https://github.com/OCA/account-financial-reporting/pull/167
* Include the download buttons inside the MIS Builder widget, and refactor
  the widget to open the door to analytic filtering in the previews.
  https://github.com/OCA/account-financial-reporting/pull/151
* Add KPI rendering prefixes (so you can print $ in front of the value).
  https://github.com/OCA/account-financial-reporting/pull/158
* Add hooks for analytic filtering.
  https://github.com/OCA/account-financial-reporting/pull/128
  https://github.com/OCA/account-financial-reporting/pull/131

8.0.0.2.0
~~~~~~~~~

Pre-history. Or rather, you need to look at the git log.
