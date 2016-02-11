# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models
from lxml import etree


class AddMisReportInstanceDashboard(models.TransientModel):
    _name = "add.mis.report.instance.dashboard.wizard"

    name = fields.Char('Name', size=32, required=True)

    dashboard_id = fields.Many2one('ir.actions.act_window',
                                   string="Dashboard", required=True,
                                   domain="[('res_model', '=', "
                                          "'board.board')]")

    @api.model
    def default_get(self, fields):
        res = {}
        if self.env.context.get('active_id', False):
            res = super(AddMisReportInstanceDashboard, self).default_get(
                fields)
            # get report instance name
            res['name'] = self.env['mis.report.instance'].browse(
                self.env.context['active_id']).name
        return res

    @api.multi
    def action_add_to_dashboard(self):
        assert self.env.context.get('active_id', False), \
            "active_id missing in context"
        # create the act_window corresponding to this report
        self.env.ref('mis_builder.mis_report_instance_result_view_form')
        view = self.env.ref(
            'mis_builder.mis_report_instance_result_view_form')
        report_result = self.env['ir.actions.act_window'].create(
            {'name': 'mis.report.instance.result.view.action.%d'
             % self.env.context['active_id'],
             'res_model': 'mis.report.instance',
             'res_id': self.env.context['active_id'],
             'target': 'current',
             'view_mode': 'form',
             'view_id': view.id})
        # add this result in the selected dashboard
        last_customization = self.env['ir.ui.view.custom'].search(
            [('user_id', '=', self.env.uid),
             ('ref_id', '=', self.dashboard_id.view_id.id)], limit=1)
        arch = self.dashboard_id.view_id.arch
        if last_customization:
            arch = self.env['ir.ui.view.custom'].browse(
                last_customization[0].id).arch
        new_arch = etree.fromstring(arch)
        column = new_arch.xpath("//column")[0]
        column.append(etree.Element('action', {'context': str(
            self.env.context),
            'name': str(report_result.id),
            'string': self.name,
            'view_mode': 'form'}))
        self.env['ir.ui.view.custom'].create(
            {'user_id': self.env.uid,
             'ref_id': self.dashboard_id.view_id.id,
             'arch': etree.tostring(new_arch, pretty_print=True)})

        return {'type': 'ir.actions.act_window_close', }
