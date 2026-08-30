# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import logging
from calendar import monthrange
from datetime import date

from odoo import Command, api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    exclude_periodic_statement = fields.Boolean(
        string="Exclude from Periodic Statement",
        company_dependent=True,
        help=(
            "If checked, this customer will not receive the monthly account statement."
        ),
    )
    last_periodic_statement_date = fields.Date(
        company_dependent=True,
        readonly=True,
    )

    def _get_periodic_statement_data(self, date_start, date_end):
        self.ensure_one()
        wiz = (
            self.env["activity.statement.wizard"]
            .with_context(active_ids=self.ids, model="res.partner")
            .create({"date_start": date_start, "date_end": date_end})
        )
        return wiz._prepare_statement()

    def _get_statement_attachment(self, date_start, date_end):
        self.ensure_one()
        iaro = self.env["ir.actions.report"]
        data = self._get_periodic_statement_data(date_start, date_end)
        report_bin, report_format = iaro._render(
            "partner_statement.activity_statement", [self.id], data=data
        )
        filename = "Statement_{}_{}.{}".format(
            self.name.replace(" ", "_"),
            date_end.strftime("%Y%m"),
            report_format,
        )
        return self.env["ir.attachment"].create(
            {
                "name": filename,
                "datas": base64.b64encode(report_bin),
            }
        )

    def _send_periodic_statement_mail(self, date_start, date_end):
        self.ensure_one()
        invoice_contact = self.address_get(["invoice"])["invoice"]
        partner = self.env["res.partner"].browse(invoice_contact)
        if not partner.email:
            _logger.warning(
                "Skipping periodic statement for %s: no email address",
                self.display_name,
            )
            return
        mail_tpl = self.env.ref(
            "partner_statement_periodic_mail_send.periodic_statement_mail_template",
            raise_if_not_found=False,
        )
        if not mail_tpl:
            return
        try:
            attach = self._get_statement_attachment(date_start, date_end)
        except Exception:
            _logger.exception(
                "Failed to render periodic statement PDF for %s", self.display_name
            )
            return
        tpl = mail_tpl.with_context(lang=partner.lang or "en_US")
        subject = tpl._render_template(tpl.subject, "res.partner", [self.id])[self.id]
        subject = "{} - {}".format(subject, date_end.strftime("%B %Y"))
        email_values = {
            "subject": subject,
            "email_to": partner.email,
            "attachment_ids": [Command.link(attach.id)],
        }
        tpl.send_mail(self.id, force_send=True, email_values=email_values)
        self.write({"last_periodic_statement_date": date_end})

    @api.model
    def _get_periodic_statement_partners(self, date_end):
        return self.search(
            [
                ("customer_rank", ">", 0),
                "|",
                ("parent_id", "=", False),
                ("is_company", "=", True),
                ("exclude_periodic_statement", "=", False),
                "|",
                ("last_periodic_statement_date", "=", False),
                ("last_periodic_statement_date", "!=", date_end),
            ]
        )

    @api.model
    def _send_periodic_statement(self, date_start=None, date_end=None):
        if date_start is None or date_end is None:
            today = fields.Date.today()
            date_start = today.replace(day=1)
            last_day = monthrange(today.year, today.month)[1]
            date_end = today.replace(day=last_day)
        customers = self._get_periodic_statement_partners(date_end)
        for customer in customers:
            customer._send_periodic_statement_mail(date_start, date_end)

    @api.model
    def _is_periodic_statement_day(self, today):
        last_day = monthrange(today.year, today.month)[1]
        return today.day == last_day

    @api.model
    def _cron_send_periodic_statement(self, day=False):
        today = date.today()
        last_day = monthrange(today.year, today.month)[1]
        if isinstance(day, int) and 1 <= day <= last_day:
            target_day = day
        elif self._is_periodic_statement_day(today):
            target_day = last_day
        else:
            return
        date_start = today.replace(day=1)
        date_end = today.replace(day=target_day)
        self._send_periodic_statement(date_start=date_start, date_end=date_end)
