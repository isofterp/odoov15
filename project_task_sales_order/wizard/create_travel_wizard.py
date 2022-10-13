# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

class MeterReadingWizardCustom(models.TransientModel):
	_name = "task.travel.wizard.custom"

	x_km_travel = fields.Integer('KM Travelled')
	x_product_id = fields.Many2one('product.product')
	x_notes = fields.Char('Travel Notes')
	x_travel_date = fields.Datetime('Travel Date', default=fields.Datetime.now,
									 help="Date and Time Travelling was done")

	def enter_travel(self):
		task_id = self._context.get('active_id')
		ptask_id = self.env['project.task'].browse(task_id)
		self.x_product_id = self.env['product.product'].search([('categ_id.name','=', 'Travel')])
		logging.warning("product is %s %s", self.x_product_id, self.x_product_id.id)
		my_user = self.env['res.users'].search([('id', '=', self.env.context.get('default_user_id', self.env.uid))])

		vals = {
			#'name': self.x_km_travel,
			#'x_equipment_id': ptask_id.project_id.x_equipment_id.id,
			#'x_task_id': task_id,
			#'product_id': self.x_product_id.id,
			'actual_qty'
			'notes': self.x_notes,
			'user_id': self.env.context.get('default_user_id', self.env.uid),

		}
		task_line = self.env['task.custom.lines'].search([('task_custom_id','=', ptask_id.id),('product_id','=', self.x_product_id.id)])
		if task_line:
			# Create a new travel line

			product = self.env['product.product'].search([('name', '=', 'Travel')])
			pricelist_id = self.env['product.pricelist'].browse([ptask_id.pricelist_id]).id
			pricelist_price = self.env['product.pricelist.item'].search(
				[('pricelist_id', '=', pricelist_id.id), ('product_tmpl_id', '=', product.id)])

			# If the job has not been quoted as yet
			# update the quoted pricing on the job aswell.
			if ptask_id.sale_order_id and ptask_id.sale_order_id.state == "draft":
				task_line.qty += self.x_km_travel
				task_line.price += self.x_km_travel * pricelist_price.fixed_price
			else:
				task_line.qty += self.x_km_travel
				task_line.price += self.x_km_travel * pricelist_price.fixed_price

			travel_notes = ''
			task_line.actual_qty += self.x_km_travel
			task_line.actual_cost += task_line.purchase_price * self.x_km_travel
			task_line.actual_profit = task_line.price - task_line.actual_cost
			if self.x_notes:
				travel_notes = self.x_notes
			if task_line.notes == "Travel" and travel_notes:
				task_line.notes += '- ' + str(self.x_travel_date) + ' ' + travel_notes
			else:
				if travel_notes:
					task_line.notes += '\n' + str(self.x_travel_date) + ' ' + travel_notes

		else:
			product = self.env['product.product'].search([('name', '=', 'Travel')])
			pricelist_id = self.env['product.pricelist'].browse([ptask_id.pricelist_id]).id
			pricelist_price = self.env['product.pricelist.item'].search(
				[('pricelist_id', '=', pricelist_id.id), ('product_tmpl_id', '=', product.id)])

			if self.x_notes:
				travel_notes = product.name + ' - ' + str(self.x_travel_date) + ' '+self.x_notes
			else:
				travel_notes = product.name

			if ptask_id.sale_order_id:
				if ptask_id.sale_order_id.state == "sale":
					quote_qty = 0
					purchase_price = 0

			vals = {
				'notes': travel_notes,
				'task_id': task_id,
				'task_custom_id': ptask_id.id,
				'product_id': product.id,
				'actual_qty': self.x_km_travel,
				'actual_cost': self.x_km_travel * product.standard_price,
				'qty': self.x_km_travel,
				# 'markup_percent': 0,
				'purchase_price': product.standard_price,
				'total_cost': product.standard_price * self.x_km_travel,
				'unit_price': pricelist_price.fixed_price,
				'price': self.x_km_travel * pricelist_price.fixed_price,
				# 'actual_profit': task_line.price - task_line.actual_cost,
				'actual_profit': (self.x_km_travel * pricelist_price.fixed_price) - (
							product.standard_price * self.x_km_travel),
				'markup_amt': (self.x_km_travel * pricelist_price.fixed_price) - (
							product.standard_price * self.x_km_travel),
				# 'markup_percent': (self.markup_amt * 100) / self.total_cost,
				'markup_percent': ((self.x_km_travel * pricelist_price.fixed_price) -
								   (product.standard_price * self.x_km_travel)) * 100 /
								  (product.standard_price * self.x_km_travel),
			}
			logging.warning("Vals is %s %s", vals.get('qty'), vals.get('actual_qty'))
			line = self.env['task.custom.lines'].create(vals)
		# Add message to chatter window of equipment and task
		msg = _(
			"""Travel KM's added for Task <strong>{task}</strong>
            created: <br/>
            <strong>KM's</strong>: {reading} <br/>
            <strong>Date</strong>: {travel_date} <br/>
            <strong>Notes</strong>: {notes} <br/>
            <strong>User</strong>: {user}
            """.format(
				task=( ptask_id.code + "-" + ptask_id.name),
				reading=self.x_km_travel,
				equipment=ptask_id.project_id.x_equipment_id.name,
				notes=self.x_notes,
				travel_date=self.x_travel_date,
				user=my_user.name,
			)
		)
		ptask_id.message_post(body=msg)
		new_stage = self.env['project.task.type'].search([('name', '=', 'WIP')])
		if ptask_id.stage_id.sequence < new_stage.sequence:
			self.env.context = dict(self.env.context)
			self.env.context.update({
				'travel_move': 'True',
			})
			ptask_id.stage_id = new_stage.id
		return
