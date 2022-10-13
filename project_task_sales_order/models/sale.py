# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    task_custom_id = fields.Many2one('project.task', string='Job Card', readonly=True, copy=False, )
    x_task_stage = fields.Many2one(related='task_custom_id.stage_id', readonly=True, string="Job Card Stage")
