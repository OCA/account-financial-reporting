# Copyright (c) 2004-2015 Odoo S.A.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)
from itertools import chain

from odoo import http
from odoo.http import request

from odoo.addons.account.controllers import download_docs


class AccountDocumentZipDownloadController(
    download_docs.AccountDocumentDownloadController
):
    @http.route(
        '/account/download_move_attachments/<models("account.move"):moves>',
        type="http",
        auth="user",
    )
    def download_move_attachments(self, moves):
        def rename_duplicates(docs):
            seen = {}
            for doc in docs:
                name = doc["filename"]
                if name not in seen:
                    seen[name] = 0
                else:
                    seen[name] += 1
                    base, *ext = name.rsplit(".", 1)
                    new_name = f"{base} ({seen[name]})" + (f".{ext[0]}" if ext else "")
                    doc["filename"] = new_name
                    seen[new_name] = 0
            return docs

        if docs_data := list(
            chain.from_iterable(move._get_move_zip_export_docs() for move in moves)
        ):
            docs_data = rename_duplicates(docs_data)
            zip_content = download_docs._build_zip_from_data(docs_data)
            headers = download_docs._get_headers(
                request.env._("Invoices") + ".zip", "zip", zip_content
            )
            return request.make_response(zip_content, headers)
