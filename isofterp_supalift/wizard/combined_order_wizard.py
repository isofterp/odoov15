from odoo import api, fields, tools, models, _

class CombinedOrderInput(models.TransientModel):
    _name = "combined.order.input.wizard"
    _description = "Input wizard"

    product_search = fields.Many2one('product.product',string='Product Search')

    def run_sql(self):
        self.env['combined.orders'].my_init(self.product_search.id)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Combined Orders',
            'res_model': 'combined.orders',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': False,
            'target': 'current',
            'nodestroy': True
        }


