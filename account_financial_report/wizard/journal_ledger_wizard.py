# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat


class JournalLedgerReportWizard(models.TransientModel):
    """Journal Ledger report wizard."""

    _name = 'journal.ledger.report.wizard'
    _description = "Journal Ledger Report Wizard"

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company',
        required=True,
        ondelete='cascade',
    )
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date range',
        domain="['|', "
               "('company_id', '=', False),"
               "('company_id', '=', company_id)]",
    )
    date_from = fields.Date(
        string="Start date",
        required=True
    )
    date_to = fields.Date(
        string="End date",
        required=True
    )
    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string="Journals",
        domain="[('company_id', '=', company_id)]",
        required=True,
    )
    move_target = fields.Selection(
        selection='_get_move_targets',
        default='all',
        required=True,
    )
    foreign_currency = fields.Boolean()
    sort_option = fields.Selection(
        selection='_get_sort_options',
        string="Sort entries by",
        default='move_name',
        required=True,
    )
    group_option = fields.Selection(
        selection='_get_group_options',
        string="Group entries by",
        default='journal',
        required=True,
    )
    with_account_name = fields.Boolean(
        default=False,
    )

    @api.model
    def _get_move_targets(self):
        return [
            ('all', _("All")),
            ('posted', _("Posted")),
            ('draft', _("Not Posted"))
        ]

    @api.model
    def _get_sort_options(self):
        return [
            ('move_name', _("Entry number")),
            ('date', _("Date")),
        ]

    @api.model
    def _get_group_options(self):
        return [
            ('journal', _("Journal")),
            ('none', _("No group")),
        ]

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'account_financial_report.action_report_journal_ledger')
        vals = action.read()[0]
        context1 = vals.get('context', {})
        if isinstance(context1, pycompat.string_types):
            context1 = safe_eval(context1)
        model = self.env['report_journal_ledger']
        report = model.create(self._prepare_report_journal_ledger())
        report.compute_data_for_report()
        context1['active_id'] = report.id
        context1['active_ids'] = report.ids
        vals['context'] = context1
        return vals

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export(report_type)

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = 'xlsx'
        return self._export(report_type)

    @api.multi
    def _prepare_report_journal_ledger(self):
        self.ensure_one()
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'move_target': self.move_target,
            'foreign_currency': self.foreign_currency,
            'company_id': self.company_id.id,
            'journal_ids': [(6, 0, self.journal_ids.ids)],
            'sort_option': self.sort_option,
            'group_option': self.group_option,
            'with_account_name': self.with_account_name,
        }

    def _export(self, report_type):
        """Default export is PDF."""
        self.ensure_one()
        model = self.env['report_journal_ledger']
        report = model.create(self._prepare_report_journal_ledger())
        report.compute_data_for_report()
        return report.print_report(report_type)
