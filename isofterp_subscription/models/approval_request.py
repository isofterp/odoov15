# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

from collections import defaultdict
import logging


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    x_project_id = fields.Many2one('project.task', 'Field Service Task')
    x_sales_order_id = fields.Many2one('sale.order', 'Sales Order')

    def action_approve(self, approver=None):
        logging.warning("=======Approval running for Cheryl")
        super(ApprovalRequest, self).action_approve()
        #print(err)
        if self.x_project_id:
            self.x_project_id.action_approve()
        if self.x_sales_order_id:
            self.x_sales_order_id.action_approve()
        if self.x_sales_order_id and self.category_id.name == 'Contract Approval':
            self.x_sales_order_id.action_quote_approve()


    def action_refuse(self, approver=None):
        super(ApprovalRequest, self).action_refuse()
        stage = self.env['project.task.type'].search([('name', '=', 'Cancelled')],limit=1).id
        if self.x_project_id:
            self.x_project_id.write({
                'x_is_refused': True,
                'x_date_refused': datetime.now(),
                'stage_id': stage,
            })
            msg = _(
                """<strong>Field Service Status -> :  {state}</strong>
                """.format(
                    state='Cancelled',
                )
            )
            self.x_project_id.message_post(body=msg)

        if self.x_sales_order_id:
            self.x_sales_order_id.write({
                'x_is_refused': True,
                'x_date_refused': datetime.now(),
                'state': 'cancel',
            })
            msg = _(
                """<strong>Sales Order Status -> :  {state}</strong>
                """.format(
                    state='Cancelled',
                )
            )
            self.x_sales_order_id.message_post(body=msg)

        # Also send an email to the owner of the task

    def action_cancel(self):
        self.sudo()._get_user_approval_activities(user=self.env.user).unlink()
        self.mapped('approver_ids').write({'status': 'cancel'})


