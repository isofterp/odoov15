# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, _
from random import random
import logging


class SaleAddPhantomBom(models.TransientModel):
    _name = 'sale.add.phantom.bom'
    _description = 'Add Kit to Quotation'

    @api.model
    def default_get(self, fields_list):
        res = super(SaleAddPhantomBom, self).default_get(fields_list)
        if self._context.get('active_model') == 'sale.order':
            res['sale_id'] = self._context['active_id']
        elif self._context.get('active_model') == 'stock.picking':
            res['picking_id'] = self._context['active_id']
        else:
            raise UserError(_(
                "The wizard can only be started from a sale order or a picking."))
        return res

    bom_id = fields.Many2one(
        'product.template', 'Kit', required=True,
        domain=[('x_kit', '=', True)])
    qty = fields.Integer(
        string='Number of Kits to Add', default=1, required=True)
    sale_id = fields.Many2one(
        'sale.order', string='Quotation')
    picking_id = fields.Many2one(
        'stock.picking', string='Picking')

    def _prepare_sale_order_line_line_section(self, main_product,sale_order):
        logging.warning("=================DOING SECTION LINE")
        qty_in_product_uom = 1
        vals = {
            'display_type': 'line_section',
            'name': main_product.name,
            'order_id': sale_order.id,
            }
        # on sale.order.line, company_id is a related field
        return vals
    def _prepare_sale_order_line_main_product(self, main_product, sale_order, wizard_qty):
        logging.warning("=================DOING MAIN PRODUCT %s", main_product.name)
        # sale_lines = self.env['sale.order.line'].search([('order_id','=',sale_order.id)])
        # if sale_lines:
        #     for sol in sale_lines:
        #         logging.warning("Lines are %s %s %s", sol.name, sol.x_kit_num, sale_order.id)
        # else:
        #     logging.warning("=== NO LINES exists")
        # print(err)
        qty_in_product_uom = 1
        #seed(1)
        unique_num = random()
        logging.warning("Random number generated %s", unique_num)
        # Search for the product in the product.product model
        product_id = self.env['product.product'].search([('product_tmpl_id','=',main_product.id)])
        vals = {
            'x_bom_parent': True,
            'product_id': product_id.id,
            'product_uom_qty': qty_in_product_uom,
            'order_id': sale_order.id,
            'x_kit_num': unique_num,
            }
        # on sale.order.line, company_id is a related field

        return vals
    @api.model
    def _prepare_sale_order_line(self, bom_line, sale_order, kit_num):
        logging.warning("=================DOING COMPONENTS LINE %s %s %s",bom_line.id,bom_line.name, bom_line.x_kit_quantity )
        product = self.env['product.product'].search([('product_tmpl_id','=',bom_line.id )])
        # qty_in_product_uom = bom_line.product_uom_id._compute_quantity(
        #     bom_line.product_qty,
        #     bom_line.product_id.uom_id)
        vals = {
            'product_id': product.id,
            #'product_uom_qty': qty_in_product_uom,
            'product_uom_qty': bom_line.x_kit_quantity,
            'order_id': sale_order.id,
            'x_kit_num': kit_num,
            }
        # on sale.order.line, company_id is a related field
        return vals

    @api.model
    def _prepare_stock_move(self, bom_line, picking, wizard_qty):
        product = bom_line.product_id
        qty_in_product_uom = bom_line.product_uom_id._compute_quantity(
            bom_line.product_qty, product.uom_id)
        vals = {
            'product_id': product.id,
            'product_uom_qty': qty_in_product_uom * wizard_qty,
            'product_uom': product.uom_id.id,
            'picking_id': picking.id,
            'company_id': picking.company_id.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'name': product.partner_ref,
            }
        return vals

    def add(self):
        self.ensure_one()
        assert self.sale_id or self.picking_id, 'No related sale_id or picking_id'
        # if self.qty < 1:
        #     raise UserError(_(
        #         "The number of kits to add must be 1 or superior"))
        assert self.bom_id.x_kit == True, 'The BOM is not a kit'
        if not self.bom_id.x_optional_component_ids:
            raise UserError(_("The selected kit has no components !"))
        prec = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        solo = self.env['sale.order.line']
        smo = self.env['stock.move']
        random_num = 0

        for main_product in self.bom_id:
            logging.warning("THE MAIN PRODUCT is %s", main_product)
            if self.sale_id:
                if self.sale_id:
                    vals = self._prepare_sale_order_line_line_section(main_product,self.sale_id)
                    solo.create(vals)
                    vals = self._prepare_sale_order_line_main_product(main_product, self.sale_id, self.qty)
                    solo.create(vals)
                    random_num = vals.get('x_kit_num')
                elif self.picking_id:
                    vals = self._prepare_stock_move(main_product, self.picking_id, self.qty)
                    smo.create(vals)

        for line in self.bom_id.x_optional_component_ids:
            # product = self.env['product.product'].search([('product_tmpl_id','=',line.id )])
            # if product:
            #     logging.warning("PRODUCT is %s", product.name, product.)
            # if float_is_zero(line.product_qty, precision_digits=prec):
            #     continue
            # The onchange is played in the inherit of the create()
            # of sale order line in the 'sale' module
            # TODO: if needed, we could increment existing order lines
            # with the same product instead of always creating new lines
            logging.warning("====LINE IS %s", line)
            if self.sale_id:
                vals = self._prepare_sale_order_line(line, self.sale_id, random_num)
                logging.warning("====CREATING COMPONENT LINE NEXT")
                solo.create(vals)
                logging.warning("====CREATED COMPONENT LINE NEXT")
            elif self.picking_id:
                vals = self._prepare_stock_move(line, self.picking_id, self.qty)
                smo.create(vals)
        return True
