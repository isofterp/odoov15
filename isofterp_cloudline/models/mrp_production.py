# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    # def _list_manufactured_products(self):
    #     print("in defautl")
    #     ids = self.env['product.template'].search([('categ_id','=','In-House')])
    #     print(ids)
    #     return

    product_id = fields.Many2one('product.product',domain="[('categ_id.name','=','In-House')]", string='Product')

class MrpBom(models.Model):
    """ Bill of Materials """
    _inherit = 'mrp.bom'

    bom_instructions = fields.Char(string="Work Instructions")