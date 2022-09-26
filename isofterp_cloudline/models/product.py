# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

class ProductProduct(models.Model):
    _inherit = "product.product"

    categ_id = fields.Many2one(related='product_tmpl_id.categ_id', string='Category')

    # @api.model
    # def create(self, vals):
    #     if 'name' in vals:
    #         self._check_for_duplicates('name', vals['name'])
    #     if 'default_code' in vals:
    #         self._check_for_duplicates('code', vals['default_code'])
    #     return super(ProductProduct, self).create(vals)
    #
    # def write(self, vals):
    #     if 'name' in vals:
    #         self._check_for_duplicates('name', vals['name'])
    #     if 'default_code' in vals:
    #         self._check_for_duplicates('code', vals['default_code'])
    #     return super(ProductProduct, self).write(vals)
    #
    # def _check_for_duplicates(self, type, value):
    #
    #     if type == 'name':
    #         rec = self.env['product.template'].search([('name', '=ilike', value)])
    #     else:
    #         rec = self.env['product.template'].search([('default_code', '=ilike', value)])
    #     if rec:
    #         if type == 'name':
    #             raise ValidationError('A Product named ' + rec.name + ' already exists ')
    #         else:
    #             raise ValidationError('A Product code ' + rec.default_code + ' already exists ')

class ProductTemplate(models.Model):
    _inherit = "product.template"
    #
    # _sql_constraints = [
    #     ('name_unique', 'unique(name)', 'cne already exists!')
    # ]
    _sql_constraints = [
        (
            "default_code_uniq",
            "unique(default_code)",
            "Internal Reference must be unique across all products!",
        )
    ]

    @api.model
    def create(self, vals):
        logging.warning("----the vals are %s", vals)
        if 'name' in vals.keys():
            self._check_for_duplicates('name',vals.get('name'))
        if 'default_code' in vals.keys():
            if vals.get('default_code'):
                self._check_for_duplicates('code',vals.get('default_code'))
        return super(ProductTemplate, self).create(vals)

    def write(self,vals):
        logging.warning("----WRITE the vals are %s", vals)
        print(err)
        if 'name' in vals:
            self._check_for_duplicates('name', vals['name'])
        if 'default_code' in vals:
            self._check_for_duplicates('code', vals['default_code'])
        return super(ProductTemplate,self).write(vals)

    def _check_for_duplicates(self,type,value):

        logging.warning("---Firing this function %s %s", type, value)
        if type == 'name':
            rec = self.env['product.template'].search([('name', '=', value)])
            print("The rec is %s", rec)
        else:
            rec = self.env['product.template'].search([('default_code', '=ilike', value)])
        if rec:
            if type == 'name':
                raise ValidationError('A Product named ' + rec.name + ' already exists ')

            else:
                raise ValidationError('A Product code ' + rec.default_code + ' already exists ')


