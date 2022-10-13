# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime


class ProjectTaskCreateTimesheet(models.TransientModel):
    _inherit = "project.task.create.timesheet"

    x_product_id = fields.Many2one(
        'product.product',
        string="Labour",
        required=True
    )

    def save_timesheet(self):
        values = {
            'task_id': self.task_id.id,
            'project_id': self.task_id.project_id.id,
            'date': fields.Date.context_today(self),
            'name': self.description,
            'user_id': self.env.uid,
            'unit_amount': self.time_spent,
            'product_id': self.x_product_id.id,
        }
        self.task_id.user_timer_id.unlink()
        return self.env['account.analytic.line'].create(values)
