
from odoo.tools.translate import _
from odoo import api, fields, models, _


class AccountConfig(models.TransientModel):
	_inherit = "res.config.settings"


	create_move_from_invoice = fields.Boolean('Create Stock Move Or Picking From Invoice',related="company_id.create_move_from_invoice",readonly=False)
	
	warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse",check_company=True,related="company_id.warehouse_id",readonly=False)

	create_move_picking = fields.Selection([('create_move','Create Stock Move From Invoice'),
		('create_picking','Create Stock Picking From Invoice')],related="company_id.create_move_picking",
		string="Create Stock Move Or Picking From Invoice",readonly=False)


