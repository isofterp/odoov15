# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class Task(models.Model):
    _description = "Task"
    _inherit = 'project.task'

    overdue_invoice_count = fields.Integer(
        compute="_compute_overdue_invoice_count_amount",
        string="# of Overdue Invoices",
        compute_sudo=True,
    )
    overdue_invoice_amount = fields.Monetary(
        compute="_compute_overdue_invoice_count_amount",
        string="Overdue Invoices Residual",
        compute_sudo=True,
        currency_field="company_currency_id",
        help="Overdue invoices total residual amount of the invoicing partner "
             "in company currency.",
    )
    company_currency_id = fields.Many2one(
        related="company_id.currency_id", store=True, string="Company Currency"
    )
    commercial_partner_invoicing_id = fields.Many2one(
        related="partner_id.commercial_partner_id",
        string="Commercial Invoicing Partner",
    )
    x_to_approve = fields.Boolean('To Approve', readonly=1, copy=False)
    x_is_approved = fields.Boolean('Is Approved', readonly=1, copy=False)
    x_date_approve = fields.Datetime('Approval Date', readonly=1, index=True, copy=False)
    x_is_refused = fields.Boolean('Is Refused', readonly=1, copy=False)
    x_date_refused = fields.Datetime('Refused Date', readonly=1, index=True, copy=False)


    def _compute_overdue_invoice_count_amount(self):
        for task in self:
            company_id = task.company_id.id or task.env.company.id
            (
                count,
                amount_company_currency,
            ) = task._prepare_overdue_invoice_count_amount(company_id)
            task.overdue_invoice_count = count
            task.overdue_invoice_amount = amount_company_currency

    def _prepare_overdue_invoice_count_amount(self, company_id):
        # This method is also called by the module
        # account_invoice_overdue_warn_sale where the company_id arg is used
        self.ensure_one()
        domain = self._prepare_overdue_invoice_domain(company_id)
        # amount_residual_signed is in company currency
        rg_res = self.env["account.move"].read_group(
            domain, ["amount_residual_signed"], []
        )
        count = 0
        overdue_invoice_amount = 0.0
        if rg_res:
            count = rg_res[0]["__count"]
            overdue_invoice_amount = rg_res[0]["amount_residual_signed"]
        return (count, overdue_invoice_amount)

    def _prepare_overdue_invoice_domain(self, company_id):
        # The use of commercial_partner_id is in this method
        self.ensure_one()
        today = fields.Date.context_today(self)
        if company_id is None:
            company_id = self.env.company.id
        domain = [
            ("move_type", "=", "out_invoice"),
            ("company_id", "=", company_id),
            ("commercial_partner_id", "=", self.commercial_partner_id.id),
            ("invoice_date_due", "<", today),
            ("state", "=", "posted"),
            ("payment_state", "in", ("not_paid", "partial")),
        ]
        return domain
    def _prepare_jump_to_overdue_invoices(self, company_id):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        action["domain"] = self._prepare_overdue_invoice_domain(company_id)
        action["context"] = {
            "journal_type": "sale",
            "move_type": "out_invoice",
            "default_move_type": "out_invoice",
            "default_partner_id": self.id,
        }
        return action

    def jump_to_overdue_invoices(self):
        self.ensure_one()
        company_id = self.company_id.id or self.env.company.id
        action = self._prepare_jump_to_overdue_invoices(company_id)
        return action

    def is_to_approve(self):
        self.ensure_one()
        #
        return self.overdue_invoice_amount > 0

    def create(self, vals):
        obj = super().create(vals)
        if obj.is_to_approve():
            # Search for the approval stage and set it
            stage = self.env['project.task.type'].search([('name','=', 'To Approve')]).id
            obj.stage_id = stage
            obj.x_to_approve = True

            # Notify Approvers
            msg = _(
                """<strong>Field Service Status -> :  {state}</strong>
                """.format(
                    state='To Approve',
                )
            )
            #obj.message_post(body=msg)

            # Send an inbox message to approvers
            val_list = {
                'Task': obj.name + " " + " is waiting to be approved",
                'Customer': obj.partner_id.name,
                'Date': obj.create_date,

            }

            partners_to_message = []
            approval_id = self.env['approval.category'].search([('name','=', 'Field Service')])
            if approval_id:
                for approver in approval_id.approver_ids:
                    logging.warning("Approvers are %s",approver.user_id)
                    partners_to_message.append(approver.user_id.partner_id.id)
                    for partner in partners_to_message:
                        notification_ids = [(0, 0, {
                            'res_partner_id': partner,
                            'notification_type': 'inbox'})]
                        #obj.message_post(body=val_list['Task'], notification_ids=notification_ids)
                        self.env['mail.activity'].create({
                            'display_name': 'Field Service Task to Approve',
                            'summary': 'Field Service Task to Approve',
                            'date_deadline': datetime.now(),
                            'user_id': approver.user_id.id,
                            'res_id': obj.id,
                            'res_model_id': 705,
                            'activity_type_id': 4

                        })
            #self._send_message(obj)

            # Create an approval request and submit it
            approval_category = self.env['approval.category'].search([('name','=', 'Field Service')])
            logging.warning("Category is %s", approval_category)
            approval_reason = 'Customer: ' + obj.partner_id.name + " has outstanding invoices older than 30 days amounting to " + str(obj.overdue_invoice_amount)
            vals_list = {
                'name': obj.name,
                'request_owner_id': obj.create_uid.id,
                'category_id':approval_category.id,
                'reason': approval_reason,
                'partner_id': obj.partner_id.id,
                'x_project_id': obj.id,
            }
            approve_request = self.env['approval.request'].create(vals_list)
            approve_request.action_confirm()
        else:
            stage = self.env['project.task.type'].search([('name', '=', 'New')]).id
            obj.stage_id = stage
        return obj

    def _send_message(self, task_rec):
        task = task_rec.name
        channel_odoo_bot_users = '%s' % ('Approvers')
        channel_obj = self.env['mail.channel']
        channel_id = channel_obj.search([('name', 'like', channel_odoo_bot_users)])

        try:

            channel_id.sudo().message_post(
                subject="Task Requires Approval " + task,
                body="Field Service Task requires approval " + task,
                message_type='comment',
                subtype_id=1,
            )
        except Exception as e:
            print('ERROR in _send_message')

    def action_approve(self):
        stage = self.env['project.task.type'].search([('name', '=', 'New')]).id
        self.write({'stage_id': stage,
                    'x_date_approve' : fields.Datetime.now(),
                    'x_to_approve': False,
                    'x_is_approved': True,})
        msg = _(
            """<strong>Field Service Task Approved by:  {user}</strong>
            """.format(
                user=self.env.user.name,
            )
        )
        self.message_post(body=msg)

    def write(self, vals):
        if 'stage_id' in vals:
            updated_stage = self.env['project.task.type'].search([('id', '=', vals.get('stage_id'))])
            if updated_stage.name == "To Approve" and self.x_date_approve:
                raise UserError(
                    _("You cannot approve a task that has already been approved %s -> %s") % (self._origin.stage_id.name, updated_stage.name))

            if updated_stage.name == "To Approve" and self.is_to_approve() != True:
                raise UserError(
                    _("You cannot move this task to an approval stage as there are no outstanding invoices %s -> %s") % (
                    self._origin.stage_id.name, updated_stage.name))

        res = super(Task, self).write(vals)
