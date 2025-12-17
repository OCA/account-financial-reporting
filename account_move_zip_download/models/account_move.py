# Copyright (c) 2004-2015 Odoo S.A.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo import _, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_move_download_all(self):
        return {
            "type": "ir.actions.act_url",
            "url": "/account/download_move_attachments/"
            f'{",".join(str(move_id) for move_id in self.ids)}',
            "target": "download",
        }

    def get_extra_print_items(self):
        """
        Helper to dynamically add items in the 'Print' menu
        of list and form of account.move.
        """
        # TO OVERRIDE
        if moves_to_export := self.filtered(lambda m: m._get_move_zip_export_docs()):
            return [
                {
                    "key": "download_all",
                    "description": _("Export ZIP"),
                    **moves_to_export.action_move_download_all(),
                },
            ]
        return []

    def _get_move_zip_export_docs(self):
        self.ensure_one()

        if self.state != "posted":
            return []

        if self.is_purchase_document(include_receipts=True):
            attachment = self.message_main_attachment_id
            return (
                [
                    {
                        "filename": attachment.name,
                        "filetype": attachment.mimetype,
                        "content": attachment.raw,
                    }
                ]
                if attachment
                else []
            )

        return self._get_invoice_legal_documents_all()
