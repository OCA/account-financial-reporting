# Copyright 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AbstractReport(models.AbstractModel):
    _inherit = "report.account_financial_report.abstract_report"

    def _get_tags_data(self, tag_ids):
        """Load name data for the given tag IDs.

        active_test=False keeps archived tags visible in historical reports.
        """
        if not tag_ids:
            return {}
        tags = (
            self.env["account.analytic.tag"]
            .with_context(active_test=False)
            .browse(list(tag_ids))
        )
        return {tag.id: {"name": tag.name} for tag in tags}

    def _build_tag_display(self, tag_ids, tags_data):
        """Return a comma-separated list of tag names for a move line."""
        names = [tags_data[tid]["name"] for tid in (tag_ids or []) if tid in tags_data]
        return ", ".join(names)
