from odoo import models, fields, api, _
from odoo.osv import expression
import re
from odoo.osv.expression import get_unaccent_wrapper


class PartnerCategory(models.Model):
    _name = 'category.customer'
    _description = 'category customer'
    _rec_name = 'complete_name'
    _order = 'complete_name'
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)
    name = fields.Char(string="Name", required=True, index=True)

    @api.depends('name', 'complete_name')
    def _compute_complete_name(self):
        for category in self:
                category.complete_name = category.name

    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     args = args or []
    #     domain = []
    #     if name:
    #         domain = ['|', ('name', operator, name), ('code', operator, name)]
    #     return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)


class Partner(models.Model):
    _inherit = 'res.partner'
    categ_id = fields.Many2one("category.customer", string="Customer Class", required=False, store=True )

class Sale(models.Model):
    _inherit = 'sale.order'

    #categ_id = fields.Many2one("category.customer", string="Customer Class", required=False)
    categ_id = fields.Char(related='partner_id.categ_id.name', string='Customer Class')

class Task(models.Model):
    _description = "Task"
    _inherit = 'project.task'

    categ_id = fields.Char(related='partner_id.categ_id.name', string='Class', store=True)

# class SaleReport(models.Model):
#     _inherit = "sale.report"
#
#     partner_categ_id = fields.Many2one('category.customer', 'Customer Category', readonly=True)
#
#     def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
#         fields['categ_id'] = ', s.categ_id as partner_categ_id'
#         groupby += ', s.categ_id'
#         return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)