# -*- coding: utf-8 -*-
# © 2014-2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import openerp.tests.common as common


class TestFetchQuery(common.TransactionCase):

    def test_fetch_query(self):
        # create a report on account.analytic.line
        data = self.registry('mis.report.instance').compute(
            self.cr, self.uid,
            self.ref('mis_builder.mis_report_instance_test'))
        self.maxDiff = None
        self.assertEquals(
            {'body':
                [{'label': u'total test',
                  'description': '',
                  'style': None,
                  'parent_row_id': None,
                  'row_id': u'total_test',
                  'cells': [{'val': 0,
                             'val_r': u'0',
                             'val_c': u'total_test = len(test)',
                             'style': None,
                             }]
                  }],
             'header':
                 [{'cols': [{'description': '07/31/2014',
                             'label': u'today',
                             'colspan': 1,
                             }],
                   },
                  {'cols': [{'label': '',
                             'description': '',
                             'colspan': 1,
                             }],
                   },
                  ],
             }, data)
