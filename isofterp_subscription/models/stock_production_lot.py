# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


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


    x_main_product = fields.Boolean('Main Product')
    x_cost_price = fields.Float('Cost Price')
    x_list_price = fields.Float('List Price')
    x_subscription_id = fields.Many2one('sale.subscription','Subscription')
    x_dlv_id = fields.Many2one('res.partner', 'Delivery Address')
    x_increase_rental_date = fields.Date('Increase Rental Date')
    x_increase_rental_percent = fields.Float(string='Increase Rental %')
    x_increase_service_date = fields.Date('Increase Service Date')
    x_increase_service_percent = fields.Float(string='Increase Service %')
    x_increase_copies_date = fields.Date('Increase Copy Date')
    x_increase_copies_percent = fields.Float(string='Increase Copy %')
    x_in_use = fields.Boolean('Machine Allocated')
    x_service_type_id = fields.Many2one('subscription.rental.group','Service Type',  domain="[('group_type','=', 'V')]")



