# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         new_name = vals.get('name')
    #       #Now create a Analytic Tag for this Serial Number
    #     rec = self.env['account.analytic.account'].search([('name', '=',self.name)])
    #     if not rec:
    #         self.env['account.analytic.account'].create({'name': new_name})
    #     return super(ProductionLot, self).create(vals_list)
    product_qty = fields.Float('Quantity', compute='_product_qty', store=True)
    x_main_product = fields.Boolean('Main Product')
    x_cost_price = fields.Float('Cost Price')
    x_list_price = fields.Float('List Price')
    x_subscription_id = fields.Many2one('sale.subscription','Subscription', )
    x_dlv_id = fields.Many2one('res.partner', 'Delivery Address')
    x_increase_rental_date = fields.Date('Increase Rental Date')
    x_increase_rental_percent = fields.Float(string='Increase Rental %')
    x_increase_service_date = fields.Date('Increase Service Date')
    x_increase_service_percent = fields.Float(string='Increase Service %')
    x_increase_copies_date = fields.Date('Increase Copy Date')
    x_increase_copies_percent = fields.Float(string='Increase Copy %')
    x_service_type_id = fields.Many2one('subscription.rental.group','Service Type',  domain="[('group_type','=', 'V')]")
    # delv_addr_ids = fields.Many2many(
    #     comodel_name="res.partner", compute="_compute_delv_addr_ids", store=True
    # )
    #
    # @api.depends("partner_id", "quant_ids.location_id", "quant_ids.quantity")
    # def _compute_delv_addr_ids(self):
    #     for lot in self:
    #         lot.x_dlv_id = self.parent.partner_id
    #         lot.delv_addr_ids = lot.quant_ids.filtered(lambda l: l.quantity > 0).mapped(
    #             "location_id"
    #         )
    def check_for_analytic_accounts(self):
        logging.warning("====Analytic accout checker running")
        lots = self.env['stock.production.lot'].search([])
        lot_count = 0
        lot_no_an = 0
        if lots:
            for lot in lots:
                #logging.warning("The lots are %s", lot.name)
                if lot.x_subscription_id and lot.x_main_product:
                    #Check if the lot has an analytic account
                    logging.warning("Working with Lot = %s [%s]", lot.name, lot.x_subscription_id.mapped('name'))
                    an_acc = self.env['account.analytic.account'].search([('name','=', lot.name)])
                    if not an_acc:
                        logging.warning("Could not find an analytic account for this serial - Creating %s", lot.name)
                        an_acc.create({
                            'name': lot.name,
                            'group_id': 1,
                            'partner_id': lot.x_dlv_id.parent_id.id,

                        })
                        lot_no_an += 1
                    lot_count += 1
        logging.warning("Lot count available is %s missing for lots %s", lot_count, lot_no_an)

    @api.model_create_multi
    def create(self, vals_list):
        self._check_create()
        logging.warning("Create - Stock Production Lot vals is %s", vals_list)

        lot = super(ProductionLot, self.with_context(mail_create_nosubscribe=True)).create(vals_list)
        if len(vals_list) != 0:
            product_id = vals_list[0].get('product_id')
            product_category = self.env['product.product'].search([('id','=',vals_list[0].get('product_id'))]).product_tmpl_id.categ_id.name
            if product_category == 'main product':
                lot.write({'x_main_product': True})
        return lot

class StockMove(models.Model):
    _inherit = 'stock.move'

    x_copies_black = fields.Char(string='Meter Reading (B&W)', readonly=True)
    x_copies_color = fields.Char(string='Meter Reading (Color)', readonly=True)


