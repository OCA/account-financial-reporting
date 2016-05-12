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
        self.assertEquals(
            {'content':
                [{'description': u'total test',
                  'comment': '',
                  'style': None,
                  'parent_row_id': None,
                  'row_id': u'total_test',
                  'cols': [{'val': 0,
                            'val_r': u'\xa00\xa0',
                            'val_c': u'total_test = len(test)',
                            }]
                  }],
             'header':
                 [{'cols': [{'comment': '07/31/2014',
                             'colspan': 1,
                             'description': u'today',
                             }],
                   },
                  {'cols': [{'colspan': 1,
                             'description': '',
                             'comment': '',
                             }],
                   },
                  ],
             }, data)
