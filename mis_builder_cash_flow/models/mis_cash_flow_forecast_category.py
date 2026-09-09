# © 2026 Solvos Consultoría Informática (<http://www.solvos.es>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import api, fields, models


class MisCashFlowForecastCategory(models.Model):
    _name = "mis.cash.flow.forecast.category"
    _description = "Cash Flow Forecast Line Category"
    _parent_store = True
    _rec_name = "complete_name"
    _order = "parent_path"

    name = fields.Char(required=True, translate=True)
    parent_id = fields.Many2one(
        "mis.cash.flow.forecast.category",
        string="Parent Category",
        ondelete="cascade",
        index=True,
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        "mis.cash.flow.forecast.category", "parent_id", string="Child Categories"
    )
    complete_name = fields.Char(compute="_compute_complete_name", store=True)

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = (
                    f"{category.parent_id.complete_name} / {category.name}"
                )
            else:
                category.complete_name = category.name
