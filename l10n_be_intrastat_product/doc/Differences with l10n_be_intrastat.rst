Differences with l10n_be_intrastat
==================================

- This modules is based upon the community framework for Intrastat declarations (intrastat_base, intrastat_product)

- The data can be retrieved from two sources: stock moves or invoices. The data source is configured on the Company record.

- The company KBO/BCE number is retrieved from the company's 'registry_number' field, a field added to the company's
  partner record by the 'l10n_be_partner' module.

