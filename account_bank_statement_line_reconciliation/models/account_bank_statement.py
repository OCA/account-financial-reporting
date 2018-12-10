# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api
from odoo.osv import expression

class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"


    def get_move_lines_for_reconciliation(
        self, excluded_ids=None, str=False, offset=0, limit=None,
        additional_domain=None, overlook_partner=False
    ):
        """
        Change the additional_domain to just see account statement line
        with date after 'Bank Reconciliation Threshold' date
        """

        additional_domain = additional_domain or []
        rec_start = self.env.user.company_id.account_bank_reconciliation_start
        if rec_start:
            additional_domain.append(('date', '>', rec_start))

        return super(
            AccountBankStatementLine, self
        ).get_move_lines_for_reconciliation(
            excluded_ids=excluded_ids,
            str=str,
            offset=offset,
            limit=limit,
            additional_domain=additional_domain,
            overlook_partner=overlook_partner
        )

    @api.multi
    def get_data_for_reconciliation_widget(self, excluded_ids=None):
        """
        Keep account bank statement line only if date line is after
        'Bank Reconciliation Threshold' date
        """

        excluded_ids = excluded_ids or []
        rec_start = self.env.user.company_id.account_bank_reconciliation_start
        ret = []
        acc_bank_st_lines = super(
            AccountBankStatementLine, self
        ).get_data_for_reconciliation_widget(excluded_ids)

        if rec_start:
            for acc_bank_st_line in acc_bank_st_lines:
                st_line_date = acc_bank_st_line['st_line']['date']
                if st_line_date > rec_start:
                    ret.append(acc_bank_st_line)
        else:
            ret = acc_bank_st_lines

        return ret
