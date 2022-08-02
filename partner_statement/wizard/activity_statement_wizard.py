# Copyright 2018 ForgeFlow, S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import base64

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class ActivityStatementWizard(models.TransientModel):
    """Activity Statement wizard."""

    _inherit = "statement.common.wizard"
    _name = "activity.statement.wizard"
    _description = "Activity Statement Wizard"

    @api.model
    def _get_date_start(self):
        return (
            fields.Date.context_today(self).replace(day=1) - relativedelta(days=1)
        ).replace(day=1)

    date_start = fields.Date(required=True, default=_get_date_start)

    @api.onchange("aging_type")
    def onchange_aging_type(self):
        super().onchange_aging_type()
        if self.aging_type == "months":
            self.date_start = self.date_end.replace(day=1)
        else:
            self.date_start = self.date_end - relativedelta(days=30)

    def _prepare_statement(self):
        res = super()._prepare_statement()
        res.update({"date_start": self.date_start})
        return res

    def _print_report(self, report_type):
        self.ensure_one()
        data = self._prepare_statement()
        if report_type == "xlsx":
            report_name = "p_s.report_activity_statement_xlsx"
        else:
            report_name = "partner_statement.activity_statement"
        if self.email_customer:
            self._send_email(report_type, report_name, data)
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
            .report_action(self, data=data)
        )

    def _send_email(self, report_type, report_name, data):
        template = self.env.ref('partner_statement.customer_statement_email_template')
        body = dict({})
        attachment_ids = []
        receipt_list = []

        if not template:
            _logger.debug("template not set, creating from template")
            template = self.env.ref('partner_statement.customer_statement_email_template')
        if not body:
            _logger.debug("body not set, creating from template")
            body = template.body_html
        _logger.debug("self examine: %s, %s", str(self), dir(self))
        for rec in self:
            _logger.debug("rec examine: %s, %s", str(rec), dir(rec))
            _logger.debug("rec.start_date examine: %s, %s", str(rec.date_start), dir(rec.date_start))
            _logger.debug("rec.email_customer examine: %s, %s", str(rec.email_customer), dir(rec.email_customer))
            _logger.debug("rec.company_id examine: %s, %s", str(rec.company_id), dir(rec.company_id))
            for partner in self._context["active_ids"]:

                customer_to_email = self.env['res.partner'].search([('id', '=', partner)])
                # add to receipt list, so all the followers get this message
                receipt_list.append(customer_to_email.email)

        receipt_list = sorted(set(receipt_list))

        full_customer_name = customer_to_email.name_get()[0][1].split(", ")
        if full_customer_name[1]:
            customer_name = f"{full_customer_name[1]}</strong> from <strong>{full_customer_name[0]}"
        else:
            customer_name = customer_to_email.name_get()[0][1]
        our_name = self.company_id.name_get()[0][1]

        body = body.replace('--CUSTOMER--', f"<strong>{customer_name}</strong>")
        body = body.replace('--SENDER--', f"<strong>{our_name}</strong>")
        body = body.replace('--DATE--', f"<strong>{self.date_start.strftime('%A the %d-%B-%Y')}</strong><br/> \n <br/>")

        attachment_ids.append(self._action_get_attachment(report_type, report_name, data).id)

        template.email_from = receipt_list[0]
        if template:
            for recipient in receipt_list:
                email_values = {
                    'subject': template.subject,
                    'body_html': body,
                    'email_to': recipient,
                    'email_from': template.email_from,
                    'attachment_ids': attachment_ids,
                    'auto_delete': True,
                }
                self.env['mail.mail'].create(email_values)

    def _export(self, report_type):
        """Default export is PDF."""
        return self._print_report(report_type)

    def _action_get_attachment(self, report_type, report_name, data):
        """ this method called from button action in view xml """
        if report_type == "xlsx":
            # report.with_context(["active_ids"]).render_qweb_pdf(docids, data=data)[0]

            attach = self.env.ref('p_s.report_activity_statement_xlsx').render_xlsx(self.ids)
        else:
            # attach = self.render_qweb_pdf(self.ids)

            # THIS ONE
            report_name = 'partner_statement.activity_statement'
            (attach, header) = self.env["ir.actions.report"].search([("report_name", "=", report_name), ("report_type", "=", report_type)], limit=1).render_qweb_pdf(self._context["active_ids"])
            # attach = self.env.ref('module_name.record_id').report_action(self, data=data, config=False)

            # attach = self.env["ir.actions.report"].search([("report_name", "=", report_name), ("report_type", "=", report_type)], limit=1).report_action(self, data=data, config=False)

        if not attach:
            _logger.debug("attachment empty")
        else:
            _logger.debug("attachment is, %s, dir: %s", str(attach), dir(attach))
            b64_attach = base64.b64encode(attach)
        # save pdf as attachment
        name = "My Attachment"
        return self.env['ir.attachment'].create({
            'name': name,
            'type': 'binary',
            'datas': b64_attach,
            'store_fname': name,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/x-pdf'
        })
