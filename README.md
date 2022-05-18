
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/account-financial-reporting&target_branch=13.0)
[![Pre-commit Status](https://github.com/OCA/account-financial-reporting/actions/workflows/pre-commit.yml/badge.svg?branch=13.0)](https://github.com/OCA/account-financial-reporting/actions/workflows/pre-commit.yml?query=branch%3A13.0)
[![Build Status](https://github.com/OCA/account-financial-reporting/actions/workflows/test.yml/badge.svg?branch=13.0)](https://github.com/OCA/account-financial-reporting/actions/workflows/test.yml?query=branch%3A13.0)
[![codecov](https://codecov.io/gh/OCA/account-financial-reporting/branch/13.0/graph/badge.svg)](https://codecov.io/gh/OCA/account-financial-reporting)
[![Translation Status](https://translation.odoo-community.org/widgets/account-financial-reporting-13-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/account-financial-reporting-13-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Odoo account financial reports

This project aims to deal with modules related to financial reports. You'll
find modules that print legal and official reports. This includes, among
others:

* One module based on webkit and totally rewritten by camptocamp, for standard
  financial reports.
* Another based on RML completely improved by Vauxoo.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_bank_reconciliation_summary_xlsx](account_bank_reconciliation_summary_xlsx/) | 13.0.1.0.0 |  | XLSX report to help on bank reconciliation
[account_financial_report](account_financial_report/) | 13.0.1.9.2 |  | OCA Financial Reports
[account_tax_balance](account_tax_balance/) | 13.0.1.0.3 |  | Compute tax balances based on date range
[mis_builder_cash_flow](mis_builder_cash_flow/) | 13.0.1.1.1 | [![jjscarafia](https://github.com/jjscarafia.png?size=30px)](https://github.com/jjscarafia) | MIS Builder Cash Flow
[mis_template_financial_report](mis_template_financial_report/) | 13.0.1.0.0 | [![hbrunn](https://github.com/hbrunn.png?size=30px)](https://github.com/hbrunn) | Profit & Loss / Balance sheet MIS templates
[partner_statement](partner_statement/) | 13.0.1.3.0 |  | OCA Financial Reports

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
