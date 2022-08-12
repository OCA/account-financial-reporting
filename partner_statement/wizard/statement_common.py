# Copyright 2018 Graeme Gellatly
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class StatementCommon(models.AbstractModel):

    _name = "statement.common.wizard"
    _description = "Statement Reports Common Wizard"

    def _get_company(self):
        return (
            self.env["res.company"].browse(self.env.context.get("force_company"))
            or self.env.company
        )

    name = fields.Char()
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=_get_company,
        string="Company",
        required=True,
    )
    date_end = fields.Date(required=True, default=fields.Date.context_today)
    show_aging_buckets = fields.Boolean(default=True)
    email_customer = fields.Boolean(default=False)
    number_partner_ids = fields.Integer(
        default=lambda self: len(self._context["active_ids"])
    )
    filter_partners_non_due = fields.Boolean(
        string="Don't show partners with no due entries", default=True
    )
    filter_negative_balances = fields.Boolean("Exclude Negative Balances", default=True)

    aging_type = fields.Selection(
        [("days", "Age by Days"), ("months", "Age by Months")],
        string="Aging Method",
        default="days",
        required=True,
    )

    account_type = fields.Selection(
        [("receivable", "Receivable"), ("payable", "Payable")],
        string="Account type",
        default="receivable",
    )

    @api.onchange("aging_type")
    def onchange_aging_type(self):
        if self.aging_type == "months":
            self.date_end = fields.Date.context_today(self).replace(
                day=1
            ) - relativedelta(days=1)
        else:
            self.date_end = fields.Date.context_today(self)

    def _prepare_statement(self):
        self.ensure_one()
        return {
            "date_end": self.date_end,
            "company_id": self.company_id.id,
            "partner_ids": self._context["active_ids"],
            "show_aging_buckets": self.show_aging_buckets,
            "filter_non_due_partners": self.filter_partners_non_due,
            "account_type": self.account_type,
            "aging_type": self.aging_type,
            "filter_negative_balances": self.filter_negative_balances,
        }

    def button_export_html(self):
        self.ensure_one()
        report_type = "qweb-html"
        return self._export(report_type)

    def button_export_pdf(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def button_export_xlsx(self):
        self.ensure_one()
        report_type = "xlsx"
        return self._export(report_type)

    def _send_email(self, report_type, report_name, data, statement_type):
        template = self.env.ref("partner_statement.customer_statement_email_template")
        body = dict({})
        attachment_ids = []
        receipt_list = []

        if not template:
            _logger.debug("template not set.")
        if not body:
            _logger.debug("body not set, creating from template")
            body = template.body_html

        current_user = self.env["res.users"].browse(self.env.uid)
        user_name = current_user.name_get()[0][1]
        company_name = self.company_id.name_get()[0][1]
        customer_name = ""

        for partner in self._context["active_ids"]:
            customer_to_email = self.env["res.partner"].search([("id", "=", partner)])
            # add to receipt list
            receipt_list.append(customer_to_email.email)
            notification_body = f"{statement_type} statement email(with "
            if report_type == "xlsx":
                notification_body = f"{notification_body} Excel"
            else:
                notification_body = f"{notification_body} PDF"

            full_customer_name = customer_to_email.name_get()[0][1].split(", ")
            if len(full_customer_name) > 1:
                customer_name = f"{full_customer_name[1]}</strong> from <strong>"
                customer_name = f"{customer_name}{full_customer_name[0]}"
                notification_body = f"{notification_body} file attached) sent to "
                notification_body = f"{notification_body}{full_customer_name[1]}"
            else:
                customer_name = customer_to_email.name_get()[0][1]
                notification_body = (
                    f"{notification_body} file attached) sent to {customer_name}"
                )
            _logger.debug("Status: %s", str(notification_body))
            notification_body = (
                f"{notification_body} &lt;{customer_to_email.email}&gt;."
            )

            customer_to_email.message_post(body=notification_body, subtype="mt_comment")

        receipt_list = sorted(set(receipt_list))

        body = body.replace("--CUSTOMER--", f"<strong>{customer_name}</strong>")
        body = body.replace("--SENDER--", f"<strong>{company_name}</strong>")
        body = body.replace(
            "--SENDER_REGARDS--", f"<strong>{user_name}<br/>{company_name}</strong>"
        )
        body = body.replace("--STATEMENT--", f"outstanding")
        body = body.replace(
            "--DATE--",
            f"<strong>{self.date_end.strftime('%A the %d-%B-%Y')}</strong><br/> \n <br/>",
        )

        attachment_ids.append(
            self._action_get_attachment(report_type, report_name, data).id
        )

        # template.email_from = receipt_lis[0]
        if template:
            for recipient in receipt_list:
                email_values = {
                    "subject": template.subject,
                    "body_html": body,
                    "email_to": recipient,
                    "email_from": template.email_from,
                    "attachment_ids": attachment_ids,
                    "auto_delete": True,
                }
                self.env["mail.mail"].create(email_values)

    def _action_get_attachment(self, report_type, report_name, data):
        """ this method called from button action in view xml """
        if report_type == "xlsx":
            (attach, header) = (
                self.env["ir.actions.report"]
                .search(
                    [
                        ("report_name", "=", report_name),
                        ("report_type", "=", report_type),
                    ],
                    limit=1,
                )
                .render_xlsx(self._context["active_ids"], data=data)
            )
            mimetype = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            (attach, header) = (
                self.env["ir.actions.report"]
                .search(
                    [
                        ("report_name", "=", report_name),
                        ("report_type", "=", report_type),
                    ],
                    limit=1,
                )
                .render_qweb_pdf(self._context["active_ids"])
            )
            mimetype = "application/x-pdf"

        if not attach:
            _logger.debug("attachment empty")
        else:
            b64_attach = base64.b64encode(attach)
        # save pdf as attachment
        name = "My Attachment"
        return self.env["ir.attachment"].create(
            {
                "name": name,
                "type": "binary",
                "datas": b64_attach,
                "store_fname": name,
                "res_model": self._name,
                "res_id": self.id,
                "mimetype": mimetype,
            }
        )
