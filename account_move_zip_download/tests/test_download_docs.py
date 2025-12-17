# Copyright (c) 2004-2015 Odoo S.A.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from io import BytesIO
from zipfile import ZipFile

from odoo.fields import Command
from odoo.tests.common import tagged

from odoo.addons.account.tests.test_download_docs import TestDownloadDocs


@tagged("post_install", "-at_install")
class TestZipDownloadDocs(TestDownloadDocs):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        invoice_3 = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner_a.id,
                "invoice_line_ids": [Command.create({"price_unit": 100})],
                "attachment_ids": [
                    Command.create(
                        {
                            "name": "Attachment",
                            "mimetype": "application/pdf",
                            "res_model": "account.move",
                            "datas": "test",
                        }
                    )
                ],
            }
        )
        cls.invoices = cls.invoices + invoice_3
        invoice_3.action_post()
        invoice_3._generate_and_send()
        assert invoice_3.invoice_pdf_report_id

    def test_download_moves_attachments(self):
        self.authenticate(self.env.user.login, self.env.user.login)
        url = (
            "/account/download_move_attachments/"
            f'{",".join(map(str, self.invoices.ids))}'
        )
        attachment_names = sorted(
            [
                doc["filename"]
                for invoice in self.invoices
                for doc in invoice._get_invoice_legal_documents_all()
            ]
        )
        res = self.url_open(url)
        self.assertEqual(res.status_code, 200)
        with ZipFile(BytesIO(res.content)) as zip_file:
            file_names = sorted(zip_file.namelist())
            self.assertEqual(file_names, attachment_names)

    def test_download_moves_attachments_with_bills(self):
        bill = self.init_invoice("in_invoice", products=self.product_a, post=True)
        bill.message_main_attachment_id = self.env["ir.attachment"].create(
            {
                "name": "Attachment",
                "mimetype": "application/pdf",
                "res_model": "account.move",
                "datas": "test_bill",
            }
        )
        attachment_names = [bill.message_main_attachment_id.name]
        self.authenticate(self.env.user.login, self.env.user.login)
        url = f"/account/download_move_attachments/{bill.id}"
        res = self.url_open(url)
        self.assertEqual(res.status_code, 200)
        with ZipFile(BytesIO(res.content)) as zip_file:
            file_names = sorted(zip_file.namelist())
            self.assertEqual(file_names, attachment_names)

    def test_download_moves_attachments_with_duplicate_names(self):
        bill_1 = self.init_invoice("in_invoice", products=self.product_a, post=True)
        bill_2 = self.init_invoice("in_invoice", products=self.product_a, post=True)
        bill_3 = self.init_invoice("in_invoice", products=self.product_a, post=True)
        att_name = "Attachment"
        bill_1.message_main_attachment_id = self.env["ir.attachment"].create(
            {
                "name": att_name,
                "mimetype": "application/pdf",
                "res_model": "account.move",
                "datas": "test_bill",
            }
        )
        bill_2.message_main_attachment_id = self.env["ir.attachment"].create(
            {
                "name": att_name,
                "mimetype": "application/pdf",
                "res_model": "account.move",
                "datas": "test_bill",
            }
        )
        bill_3.message_main_attachment_id = self.env["ir.attachment"].create(
            {
                "name": f"{att_name} (1)",
                "mimetype": "application/pdf",
                "res_model": "account.move",
                "datas": "test_bill",
            }
        )
        attachment_names = [att_name, f"{att_name} (1)", f"{att_name} (1) (1)"]
        self.authenticate(self.env.user.login, self.env.user.login)

        url = f"/account/download_move_attachments/{bill_1.id},{bill_2.id},{bill_3.id}"
        res = self.url_open(url)
        self.assertEqual(res.status_code, 200)
        with ZipFile(BytesIO(res.content)) as zip_file:
            file_names = sorted(zip_file.namelist())
            self.assertEqual(file_names, attachment_names)

        att_name = "Attachment.ext"
        bill_1.message_main_attachment_id.name = att_name
        bill_2.message_main_attachment_id.name = att_name
        attachment_names = [
            f"{att_name.split('.')[0]} (1).{att_name.split('.')[1]}",
            att_name,
        ]

        url = f"/account/download_move_attachments/{bill_1.id},{bill_2.id}"
        res = self.url_open(url)
        with ZipFile(BytesIO(res.content)) as zip_file:
            file_names = sorted(zip_file.namelist())
            self.assertEqual(file_names, attachment_names)
