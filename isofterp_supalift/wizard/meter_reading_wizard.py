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
		task_id = self._context.get('active_id')
		ptask_id = self.env['project.task'].browse(task_id)
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

		logging.warning("equipment is %s", new_reading.x_equipment_id)
		new_reading.x_equipment_id.message_post(body=msg)

		return new_reading
