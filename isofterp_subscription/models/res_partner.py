#!/usr/bin/env python
from odoo import api, fields, models, _
import logging


class Partner(models.Model):
    _inherit = "res.partner"

    # @api.model_create_multi
    # def create(self, vals_list):
    #     partners = super(Partner, self).create(vals_list)
    #     for vals in vals_list:
    #         is_company = vals.get('company_type')
    #         account_no = vals.get('x_account_number')
    #     # Create an Analytic Account for this Customer
    #     if is_company == 'company':
    #         analytic = self.env['account.analytic.account'].create(
    #             {'name': account_no, 'partner_id': partners.id, 'group_id': 1})
    #     return partners

    x_account_number = fields.Char('Account Number', index=True, required='Yes')
    x_fax = fields.Char('Fax Number')
    x_company_reg_no = fields.Char('Company reg no')
