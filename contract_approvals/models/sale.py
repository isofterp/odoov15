# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _description = "Sales"
    _inherit = 'sale.order'

    state = fields.Selection([
        ('to_approve', 'To Approve'),
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    x_sale_approve = fields.Boolean('Management To Approve', readonly=1, copy=False)
    x_sale_approved = fields.Boolean('Management Approved', readonly=1, copy=False)
    x_sale_date_approve = fields.Datetime('Management Approval', readonly=1, index=True, copy=False)
    x_sale_refused = fields.Boolean('Refused By Management', readonly=1, copy=False)
    x_sale_date_refused = fields.Datetime('Management Refusal Date', readonly=1, index=True, copy=False)

    def _setup_fields(self):
        super(SaleOrder, self)._setup_fields()
        selection = self._fields['state'].selection
        exists = False
        for idx, (state, __) in enumerate(selection):
            if state == 'to_approve':
                exists = True
        if not exists:
            selection.insert(0, ('to_approve', _('To Approve')))
    def create(self, vals):
        obj = super().create(vals)
        if obj.x_is_contract_quote:
            # Search for the approval stage and set it
            obj.state = 'to_approve'

            # Notify Approvers
            msg = _(
                """<strong>Quotation Status -> :  {state}</strong>
                """.format(
                    state='To Approve',
                )
            )
            obj.message_post(body=msg)
            approval_category = self.env['approval.category'].search([('name', '=', 'Contract Approval')])
            logging.warning("Category is %s", approval_category)
            approval_reason = "Contract Quotation needs to be authorized by Management"

            # Send an inbox message to approvers
            vals_list = {
                'name': obj.name,
                'request_owner_id': obj.user_id.id,
                'category_id': approval_category.id,
                'reason': approval_reason,
                'partner_id': obj.partner_id.id,
                'x_sales_order_id': obj.id,
            }

            # partners_to_message = []
            # for approver in approval_category.approver_ids:
            #     logging.warning("Approvers are %s",approver.user_id)
            #     partners_to_message.append(approver.user_id.partner_id.id)
            #     for partner in partners_to_message:
            #         notification_ids = [(0, 0, {
            #             'res_partner_id': partner,
            #             'notification_type': 'inbox'})]
            #         self.env['mail.activity'].create({
            #             'display_name': 'Contract Quotation to Approve',
            #             'summary': 'Contract Quotation to Approve',
            #             'date_deadline': datetime.now(),
            #             'user_id': approver.user_id.id,
            #             'res_id': obj.id,
            #             'res_model_id': 705,
            #             'activity_type_id': 4
            #
            #             })

            approve_request = self.env['approval.request'].create(vals_list)
            approve_request.action_confirm()

        return obj


    def action_quote_approve(self):
        self.write({'state': 'draft',
                    'x_sale_date_approve': fields.Datetime.now(),
                    'x_sale_approved': True})
        msg = _(
            """<strong>Quotation Approved by:  {user}</strong>
            """.format(
                user=self.env.user.name,
            )
        )
        self.message_post(body=msg)
