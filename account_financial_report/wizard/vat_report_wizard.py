# Copyright  2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat


class VATReportWizard(models.TransientModel):
    _name = "vat.report.wizard"

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date range'
    )
    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    based_on = fields.Selection([('taxtags', 'Tax Tags'),
                                 ('taxgroups', 'Tax Groups')],
                                string='Based On',
                                required=True,
                                default='taxtags')
    tax_detail = fields.Boolean('Detail Taxes')

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'account_financial_report.action_report_vat_report')
        vals = action.read()[0]
        context1 = vals.get('context', {})
        if isinstance(context1, pycompat.string_types):
            context1 = safe_eval(context1)
        model = self.env['report_vat_report']
        report = model.create(self._prepare_vat_report())
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

    def _prepare_vat_report(self):
        self.ensure_one()
        return {
            'company_id': self.company_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'based_on': self.based_on,
            'tax_detail': self.tax_detail,
        }

    def _export(self, report_type):
        """Default export is PDF."""
        model = self.env['report_vat_report']
        report = model.create(self._prepare_vat_report())
        report.compute_data_for_report()
        return report.print_report(report_type)
