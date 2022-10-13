# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo.tools.translate import _
from odoo import api, fields, models, _
from odoo.exceptions import Warning
			

class ResCompany(models.Model):
    _inherit = "res.company"

    create_move = fields.Boolean('Create Stock Move From Invoice')
    create_picking = fields.Boolean('Create Stock Picking From Invoice')
    create_move_from_invoice = fields.Boolean('Create Stock Move Or Picking From Invoice')
    warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse",check_company=True)
    create_move_picking = fields.Selection([('create_move','Create Stock Move From Invoice'),('create_picking','Create Stock Picking From Invoice')],default="create_picking")
