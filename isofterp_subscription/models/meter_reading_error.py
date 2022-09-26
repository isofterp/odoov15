from odoo import api, fields, models, _


class MeterReadingError(models.Model):
    _name = 'meter.reading.error'
    _description = 'Meter Reading error table'

    name = fields.Char(string='Message')