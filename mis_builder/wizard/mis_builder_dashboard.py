#==============================================================================
#                                                                             =
#    mis_builder module for OpenERP, Management Information System Builder
#    Copyright (C) 2014 ACSONE SA/NV (<http://acsone.eu>)
#                                                                             =
#    This file is a part of mis_builder
#                                                                             =
#    mis_builder is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#                                                                             =
#    mis_builder is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#                                                                             =
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#                                                                             =
#==============================================================================

from openerp.osv import orm, fields
from lxml import etree


class add_mis_report_instance_dashboard(orm.TransientModel):
    _name = "add.mis.report.instance.dashboard.wizard"

    _columns = {'name': fields.char('Name', size=32, required=True),
                'dashboard_id': fields.many2one('ir.actions.act_window', string="Dashboard", required=True,
                                                domain="[('res_model', '=', 'board.board')]"),
                }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        if context.get('active_id'):
            res = super(add_mis_report_instance_dashboard, self).default_get(cr, uid, fields, context=context)
            # get report instance name
            res['name'] = self.pool['mis.report.instance'].read(cr, uid, context['active_id'], ['name'])['name']
        return res

    def action_add_to_dashboard(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        assert 'active_id' in context, "active_id missing in context"
        wizard_data = self.browse(cr, uid, ids, context=context)[0]
        # create the act_window corresponding to this report
        view_id = self.pool['ir.model.data'].get_object_reference(cr, uid, 'mis_builder', 'mis_report_instance_result_view_form')[1]
        report_result = self.pool['ir.actions.act_window'].create(cr, uid, {'name': 'mis.report.instance.result.view.action.%d' % context['active_id'],
                                                                            'res_model': 'mis.report.instance',
                                                                            'res_id': context['active_id'],
                                                                            'target': 'current',
                                                                            'view_mode': 'form',
                                                                            'view_id': view_id})
        # add this result in the selected dashboard
        last_customization = self.pool['ir.ui.view.custom'].search(cr, uid, [('user_id', '=', uid),
                                                                             ('ref_id', '=', wizard_data.dashboard_id.view_id.id)], limit=1)
        arch = wizard_data.dashboard_id.view_id.arch
        if last_customization:
            arch = self.pool['ir.ui.view.custom'].read(cr, uid, last_customization[0], ['arch'])['arch']
        new_arch = etree.fromstring(arch)
        column = new_arch.xpath("//column")[0]
        column.append(etree.Element('action', {'context': str(context),
                                         'name': str(report_result),
                                         'string': wizard_data.name,
                                         'view_mode': 'form'}))
        self.pool['ir.ui.view.custom'].create(cr, uid, {'user_id': uid,
                                                        'ref_id': wizard_data.dashboard_id.view_id.id,
                                                        'arch': etree.tostring(new_arch, pretty_print=True)})

        return {'type': 'ir.actions.act_window_close', }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
