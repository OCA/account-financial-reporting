# -*- coding: utf-8 -*-
# Copyright 2016 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from openerp.tools.misc import pickle


class AccountMove(models.Model):
    _inherit = 'account.move'

    # a pickled set of the codes of all accounts affected by the move. This
    # allows to compute the counterpart accounts field in
    # `report_general_ledger_qweb` more efficiently.
    _account_codes_cache = fields.Binary(
            compute='_compute_account_codes_cache')

    @api.depends('line_ids.account_id.code')
    def _compute_account_codes_cache(self):
        for mv in self:
            res = set(mv.mapped('line_ids.account_id.code'))
            res = list(res) # set doesn't unpickle without globals()
                            # under protocol_version <= 2
            mv._account_codes_cache = pickle.dumps(res)

    @api.multi
    def _get_account_codes(self):
        return set(pickle.loads(self._account_codes_cache))
