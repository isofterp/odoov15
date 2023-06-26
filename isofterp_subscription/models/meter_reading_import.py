from odoo import api, fields, models, _
import base64
import io
import logging
from datetime import datetime

from odoo.tools.translate import _, pycompat
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MeterReadingImport(models.TransientModel):
    _name = 'meter.reading.import'
    _description = 'Import Meter Reading'


    data_file = fields.Binary('Meter Reading File', required=True,
                                                    help='Select your Meter Reading csv file here - make sure it is the latest one !.')
    input_layout = fields.Selection([('fm',"FM Audit"),("man","Manual")],"Choose the File Format for this input", default='fm')

    def update_readings(self,black,colour):
        print(black,colour)
        return

    def import_readings(self):
        # line_obj =  self.env['sale.subscription.line']
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M")
        serial_no = ''
        lines = []

        error_obj = self.env['meter.reading.error']
        error_obj.search([]).unlink()  # Delete All prevoius messages
        line_obj = self.env['sale.subscription.line']
        csv_data = base64.b64decode(self.data_file)
        csv_input_file = pycompat.csv_reader(io.BytesIO(csv_data), quotechar='"', delimiter=',')
        err = 'Starting Import  ' + dt_string
        error_obj.create({'name': err})
        lines = []

        for row in csv_input_file:
            serial_no = row[0].strip('"')
            colour = row[1]
            black = row[2]
            line_ids = line_obj.search([('x_serial_number_id', '=', serial_no)])
            if line_ids:
                for line in line_ids:
                    if black.isdigit():
                        if line.name == 'Black copies' and int(black) > 0:
                            print('found Black copies serialnumber ', serial_no, line.name, line.analytic_account_id.name)
                            line.write({'x_copies_last': black})
                    if colour.isdigit():
                        if line.name == 'Colour copies' and int(colour) > 0:
                            print('found Colour copies serialnumber ', serial_no, line.name, line.analytic_account_id.name)
                    if self.input_layout == 'fm':
                        line.write({'x_reading_type_last': 'FM Audit'})
                    if self.input_layout == 'man':
                        line.write({'x_reading_type_last': 'Manual'})



        print('Finished')
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M")
        message = dt_string + ' Import Finished - last record was ' + serial_no
        error_obj.create({'name': message})
        return {
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'meter.reading.error',
            'target': 'current',
            'res_id': 121,
            'type': 'ir.actions.act_window'
        }
