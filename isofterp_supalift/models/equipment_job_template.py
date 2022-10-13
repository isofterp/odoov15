# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import uuid
import time
import datetime



import logging

class EquipmentJobTemplate(models.Model):
    _name = "equipment.job.template"
    _description = "Job Template"

    name = fields.Char('Equipment Job Template', required=True)
    task_template_line_ids = fields.One2many('equipment.job.template.line', 'task_template_id', 'Task Template Lines', copy=True)
    active = fields.Boolean(default=True,
                            help="If unchecked, it will allow you to hide the task template without removing it.")
    company_id = fields.Many2one('res.company', string='Company')
    equipment_cat_id = fields.Many2one('maintenance.equipment.category', 'Equipment Category')

    @api.model_create_multi
    def create(self, vals_list):
        records = super(EquipmentJobTemplate, self).create(vals_list)
        return records

class EquipmentJobTemplateLine(models.Model):
    _name = "equipment.job.template.line"
    _description = "Project Task Template Lines"

    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of sale quote lines.",
                              default=10)
    task_template_id = fields.Many2one('equipment.job.template', 'Task Template Reference', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', related='task_template_id.company_id', store=True, index=True)
    name = fields.Text('Description', required=True, translate=True)
    product_id = fields.Many2one(
        'product.product', 'Product', check_company=True,
        domain=[('sale_ok', '=', True),('can_be_expensed','=', False)])
    product_uom_qty = fields.Float('Quantity', required=True, digits='Product Unit of Measure', default=1)
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure',
                                     domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.ensure_one()
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
            self.name = self.product_id.get_product_multiline_description_sale()

    @api.model
    def create(self, values):
        return super(EquipmentJobTemplateLine, self).create(values)