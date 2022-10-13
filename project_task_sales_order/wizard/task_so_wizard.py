# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class TaskSaleWizardCustom(models.TransientModel):
	_name = "task.saleorder.wizard.custom"
	
	def create_task_saleorder(self):

		task_id = self._context.get('active_id')

		ptask_id = self.env['project.task'].browse(task_id)

		if all(rec.is_so_line_created for rec in ptask_id.task_custom_line_ids):
			raise UserError(_('No quotation product lines is found to create quotation.'))

		if not ptask_id.task_custom_line_ids:
			raise UserError(_('Please add quotation product lines to create quotation.'))

		if not ptask_id.partner_id:
			raise UserError(_('Please select customer on task to create sales quotation.'))

		vals = {
			'analytic_account_id': ptask_id.project_id.analytic_account_id.id,
			'task_custom_id': ptask_id.id,
			'partner_id': ptask_id.partner_id.id,
			'user_id': ptask_id.user_id.id,
			'pricelist_id': ptask_id.partner_id.property_product_pricelist and ptask_id.partner_id.property_product_pricelist.id or False,
			'branch_id': ptask_id.branch_id.id,
			'x_equipment_id': ptask_id.x_equipment_id.id,
		}
		#print('vals= ',vals)
		#print(err)

		order_id = self.env['sale.order'].sudo().create(vals)
		ptask_id.write({'sale_order_id': order_id.id})
		for line in ptask_id.task_custom_line_ids:
			purchase_price = 0.0
			if not line.product_id:
				raise UserError(_('Please define product on quotation product lines.'))
			if line.qty and line.price:
				price_unit = line.price / line.qty
			else:
				raise UserError(_('One or more lines dont have a quantity or unit price set. Please check'))
			# if order_id.pricelist_id:
			# 	price_unit, rule_id = order_id.pricelist_id.get_product_price_rule(
			# 		line.product_id,
			# 		line.qty or 1.0,
			# 		order_id.partner_id
			# 	)

			# Disscuss this with Christine
			# if line.actual_cost:
			# 	purchase_price = line.actual_cost
			# else:
			#purchase_price = line.total_cost

			orderlinevals = {
				'order_id' : order_id.id,
				'product_id' : line.product_id.id,
				'product_uom_qty' : line.qty,
				'product_uom' : line.product_id.uom_id.id,  #line.product_uom.id,
				'price_unit' : price_unit,
				'purchase_price': line.purchase_price,
				'name' : line.notes or line.product_id.name or '/',
				}
			
			if not line.is_so_line_created:
				line_id = self.env['sale.order.line'].create(orderlinevals)

			line.is_so_line_created = True


		action = self.env.ref('sale.action_quotations')
		result = action.sudo().read()[0]
		result['domain'] = [('id', '=', order_id.id)]
		return result