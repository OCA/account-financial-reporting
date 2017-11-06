# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class JournalReportWizard(models.TransientModel):

    _name = 'journal.report.wizard'

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
    with_currency = fields.Boolean()
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
    def export_as_pdf(self):
        self.ensure_one()
        return self._export()

    @api.multi
    def export_as_xlsx(self):
        self.ensure_one()
        return self._export(xlsx_report=True)

    @api.multi
    def _prepare_report_journal(self):
        self.ensure_one()
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'move_target': self.move_target,
            'with_currency': self.with_currency,
            'company_id': self.company_id.id,
            'journal_ids': [(6, 0, self.journal_ids.ids)],
            'sort_option': self.sort_option,
            'group_option': self.group_option,
            'with_account_name': self.with_account_name,
        }

    @api.multi
    def _export(self, xlsx_report=False):
        self.ensure_one()
        model = self.env['report_journal_qweb']
        report = model.create(self._prepare_report_journal())
        return report.print_report(xlsx_report=xlsx_report)
