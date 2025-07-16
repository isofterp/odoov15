# -*- coding: utf-8 -*-
# Copyright 2020-2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('invoice_line_ids', 'invoice_line_ids.product_id')
    def _compute_invoice_finance_charges(self):
        for invoice in self:
            finance_charge_product = self.env['ir.config_parameter'].sudo().get_param('finance_charge.product_id')
            invoice_line_products = invoice.invoice_line_ids.mapped('product_id')
            invoice.invoice_finance_charges = invoice.move_type == "out_invoice" and int(finance_charge_product) in invoice_line_products.ids or False

    invoice_finance_charges = fields.Boolean(string = 'Finance Charges invoice', readonly=True, compute="_compute_invoice_finance_charges", store=True)
