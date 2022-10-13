from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Date, Datetime
import logging

class MeterReading(models.Model):
    _name = 'meter.reading'
    _description = "Machine Meter Reading"
    # _inherit = [
    # 	"mail.thread",
    # 	"mail.activity.mixin",
    # ]

    name = fields.Integer('Reading')
    x_equipment_id = fields.Many2one('maintenance.equipment', 'Equipment',
                                      ondelete='cascade', index=True)
    x_task_id = fields.Many2one('project.task', 'Job Number')
    x_reading_date = fields.Datetime('Reading Date', default=fields.Datetime.now,
                                     help="Date and Time Reading was taken")
    x_notes = fields.Text("Log Entry Notes")
    user_id = fields.Many2one('res.users', string='Technician/User', default=lambda self: self.env.user, tracking=True)


