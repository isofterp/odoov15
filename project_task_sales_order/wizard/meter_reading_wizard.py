# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

class MeterReadingWizardCustom(models.TransientModel):
	_name = "meter.reading.wizard.custom"

	x_meter_reading = fields.Integer('Reading')
	x_notes = fields.Char('Log Entry Notes')
	x_reading_date = fields.Datetime('Reading Date', default=fields.Datetime.now,
									 help="Date and Time Reading was taken")

	def enter_meter_reading(self):

		# Find the last meeting reading and check if the current reading is less then the previous reading


		task_id = self._context.get('active_id')
		ptask_id = self.env['project.task'].browse(task_id)
		# Need to search globally and not per task
		reading_exist = self.env['meter.reading'].search([('x_task_id', '=',task_id)], limit=1, order='id desc')
		if reading_exist:
			raise UserError(_(
				"Cannot add another reading for the same job - Escalate to Manager"))
		cur_reading = self.env['meter.reading'].search([('x_equipment_id', '=', ptask_id.project_id.x_equipment_id.id)],
													   limit=1, order='id desc')
		logging.warning("Current reading is %s", cur_reading)
		if int(self.x_meter_reading) < int(cur_reading.name) and (self.x_reading_date) >= cur_reading.x_reading_date:
			raise UserError(_(
				"New reading cannot be less then previous reading - if the meter has been replaced, request an Administrator to amend the current reading."))

		my_user = self.env['res.users'].search([('id', '=', self.env.context.get('default_user_id', self.env.uid))])
		vals = {
			'name': self.x_meter_reading,
			'x_equipment_id': ptask_id.project_id.x_equipment_id.id,
			'x_task_id': task_id,
			'x_reading_date': self.x_reading_date,
			'x_notes': self.x_notes,
			'user_id': self.env.context.get('default_user_id', self.env.uid),

		}
		new_reading = self.env['meter.reading'].create(vals)

		# Add message to chatter window of equipment and task

		msg = _(
			"""Meter Reading for Task <strong>{task}</strong>
            created: <br/>
            <strong>Reading</strong>: {reading} <br/>
            <strong>Equipment</strong>: {equipment} <br/>
            <strong>Log Entry</strong>: {notes} <br/>
            <strong>User</strong>: {user}
            """.format(
				task=( ptask_id.code + "-" + ptask_id.name),
				reading=self.x_meter_reading,
				equipment=ptask_id.project_id.x_equipment_id.name,
				notes=self.x_notes,
				user=my_user.name,
			)
		)


		ptask_id.message_post(body=msg)
		# if meter reading entered - change state
		# if the PO number is entered on the job and the meter reading is being entered
		# change the state to closed
		if ptask_id.x_po_no:
			stage_id = self.env['project.task.type'].search([('name', 'like', 'Closed'), ('active', '=', True)])
		# if ptask_id.sale_order_id.state == 'draft':
		# 	stage_id = self.env['project.task.type'].search([('name', 'like', 'Awaiting PO'), ('active', '=', True)])
		if not ptask_id.x_po_no:
			stage_id = self.env['project.task.type'].search([('name', 'like', 'Completed'),('active','=', True)])
		logging.warning("stage id is %s", stage_id.name)

		if ptask_id.sale_order_id and ptask_id.sale_order_id.state == "sent":
			stage_id = self.env['project.task.type'].search([('name', '=', 'Awaiting PO')])

		# if ptask_id.stage_id != stage_id.id:
		# 	# msg = _(
		# 	# 	"""Changing state from <strong>{cur_state} to <strong>{new_state}</strong>
        #     #     """.format(
		# 	# 		cur_state=ptask_id.stage_id.name,
		# 	# 		new_state = self.client_order_ref,
		# 	# 	)
		# 	# )
		ptask_id.stage_id = stage_id.id
		ptask_id.project_id.x_meter_reading = self.x_meter_reading
		logging.warning("equipment is %s %s", new_reading.x_equipment_id, ptask_id.stage_id.name)
		new_reading.x_equipment_id.message_post(body=msg)

		return new_reading
