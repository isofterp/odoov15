# Copyright 2018 Graeme Gellatly
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
import base64
import logging


class StatementCommon(models.AbstractModel):

    _name = "statement.common.wizard"
    _description = "Statement Reports Common Wizard"

    name = fields.Char()
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        string="Company",
        required=True,
    )
    date_end = fields.Date(required=True, default=fields.Date.context_today)
    show_aging_buckets = fields.Boolean(default=True)
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

    def send_email_with_attachment(self):
        data = self._prepare_statement()

        pdf = self.env.ref("partner_statement.action_print_outstanding_statement")._render_qweb_pdf(
            self.id, data=data)

        data_record = base64.b64encode(pdf[0])

        ir_values = {
            'name': "Customer Statement.pdf",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }

        data_id = self.env['ir.attachment'].create(ir_values)
        template = self.env['mail.template'].search([('name', '=', 'Customer Statement email')])
        if template:
            logging.warning("Template is %s", template.name)
        else:
            logging.warning("Could not find the template")

        template.attachment_ids = [(6, 0, [data_id.id])]
        partner = self.env['res.partner'].search([('id', '=',data.get('partner_ids')[0])])
        email_values = {'email_to': partner.email,}
        template.with_context(email_values).send_mail(partner.id, email_values=email_values, force_send=False)
        template.attachment_ids = [(3, data_id.id)]
        return True
