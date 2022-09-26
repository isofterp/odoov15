# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class SubscriptionMachineCharge(models.Model):
    _name = "subscription.machine.charge"
    _description = "Charges for each Machine"

    @api.onchange('product_id')
    def _update_description(self):
        self.name = self.product_id.name

    def write(self, vals):
        res = super(SubscriptionMachineCharge, self).write(vals)
        print ('we are here SubscriptionMachineCharge')
        return

    name = fields.Char('Description')
    charges_type_id = fields.Many2one('subscription.charges.type', 'Transaction Type')
    product_id = fields.Many2one('product.product',string='Product')
    product_key = fields.Integer('Key')
    qty = fields.Float('Quantity')
    price = fields.Float('Price')
    minimum_charge = fields.Float('Minimum Charge')
    copies_free = fields.Integer('Free Copies')
    copies_vol_1 = fields.Integer('Volume 1')
    copies_price_1 = fields.Float('Charge 1')
    copies_vol_2 = fields.Integer('Volume 2')
    copies_price_2 = fields.Float('Charge 2')
    copies_vol_3 = fields.Integer('Volume 3')
    copies_price_3 = fields.Float('Charge 3')

