# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockLot(models.Model):
    _inherit = 'stock.production.lot'

    x_partner_id = fields.Many2one('res.partner', 'Customer')


