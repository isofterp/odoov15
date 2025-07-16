# -*- coding: utf-8 -*-
# Copyright 2020-2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_id = fields.Many2one('product.product', config_parameter='finance_charge.product_id', string="Finance Charge Product")
    finance_percent = fields.Float(config_parameter='finance_charge.finance_percent')
    payment_term_id = fields.Many2one('account.payment.term', config_parameter='finance_charge.payment_term_id')
    finance_threshold = fields.Float('Finance Threshold', config_parameter='finance_charge.finance_threshold')
