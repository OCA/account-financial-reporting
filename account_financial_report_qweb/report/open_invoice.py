# -*- coding: utf-8 -*-
# Author: Andrea andrea4ever Gallina
# Author: Francesco OpenCode Apruzzese
# Author: Ciro CiroBoxHub Urselli
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import models, api


class OpenInvoiceReport(models.AbstractModel):

    _name = 'report.account_financial_report_qweb.open_invoice_report_qweb'

    def _get_domain(self, data):
        account_type = ('payable', 'receivable')
        if data['form']['result_selection'] == 'customer':
            account_type = ('receivable', )
        elif data['form']['result_selection'] == 'supplier':
            account_type = ('payable', )
        domain = [
            ('company_id', '=', data['form']['company_id'][0]),
            ('move_id.date', '<=', data['form']['at_date']),
            ('account_id.user_type_id.type', 'in', account_type)
            ]
        if data['form']['target_move'] != 'all':
            domain.append(('move_id.state', 'in', ('posted', )), )
        if data['form']['partner_ids']:
            domain.append(('partner_id', 'in',
                           [p.id for p in data['form']['partner_ids']]), )
        return domain

    def _query(self, data):

        moves = self.env['account.move.line'].search(
            self._get_domain(data), order='date asc')
        if not moves:
            return True  # ----- Show a message here
        return moves

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        moves = self._query(data)
        docargs = {
            'doc_model': 'account.move.line',
            'doc_ids': data['ids'],
            'docs': moves,
            'header': data['header'],
            'account_obj': self.env['account.account'],
            'partner_obj': self.env['res.partner'],
            'currency_obj': self.env['res.currency'],
            }

        return report_obj.render(
            'account_financial_report_qweb.open_invoice_report_qweb',
            docargs)
