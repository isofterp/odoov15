# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_partner_dlv_street = fields.Char(related='partner_id.street', string='Street')
    x_partner_dlv_street2 = fields.Char(related='partner_id.street2', string='')
    x_partner_dlv_email = fields.Char(related='partner_id.email', string='')
    x_partner_dlv_phone = fields.Char(related='partner_id.phone', string='')
    x_partner_dlv_mobile = fields.Char(related='partner_id.mobile', string='')

