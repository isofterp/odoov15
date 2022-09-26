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
    input_layout = fields.Selection([('fm',"FM Audit"),("email","Email")],"Choose the File Format for this input", default='fm')

    def update_readings(self,black,colour):
        print(black,colour)
        return

    def import_readings(self):
        # line_obj =  self.env['sale.subscription.line']
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M")
        serial_no = ''
        lines = []
        if self.input_layout == 'fm':
            error_obj = self.env['meter.reading.error']
            error_obj.search([]).unlink()  # Delete All prevoius messages
            line_obj = self.env['sale.subscription.line']
            csv_data = base64.b64decode(self.data_file)
            csv_input_file = pycompat.csv_reader(io.BytesIO(csv_data), quotechar='"', delimiter=',')
            err = 'Starting Import  ' + dt_string
            error_obj.create({'name': err})
            lines = []
            """
            #try:
            #SQL_select = "SELECT l.id,l.name,s.x_copies_previous, s.name ,s.id  " \
            #      "FROM stock_production_lot as l, sale_subscription_line as s " \
            #      "WHERE (s.name = 'Black copies' OR s.name = 'Colour copies') AND l.name = %s AND s.x_serial_number_id = l.id"
            SQL_select = "SELECT s.x_copies_previous, s.name ,s.id  " \
                         "FROM stock_production_lot as l " \
                         "JOIN sale_subscription_line as s ON s.x_serial_number_id = l.id " \
                         "WHERE s.name = 'Black copies' OR s.name = 'Colour copies' AND l.name = %s"
            SQL_write = "UPDATE sale_subscription_line SET x_copies_last = %s, quantity = %s WHERE id = %s"
            for row in csv_iterator:
                serial_no = row[0].strip('"')
                if row[0] == 'serial_no':continue
                if row[0] != 'S7214300104': continue
                colour = row[1]
                black = row[2]
                print(row[0])
                self._cr.execute(SQL_select % ("'" + row[0] +  "'" ) )
                lines = self._cr.fetchall()
                print(lines)
                print('@ 56', row[0], row[1], row[2])
                if lines:
                    for line in lines:
                        if line[1] == 'Black copies' and int(black) > 0:
                            copies = black
                        if line[1] == 'Colour copies' and int(colour) > 0:
                            copies  = colour
                        #print('@ 61',row[0],row[1],row[2])
                        quantity =   int(copies) - line[2]

                        self._cr.execute(SQL_write % ( copies ,str(quantity), line[2]))
                        #print(line[4])
                else:
                    #print ('No Invoice line found for seriral number ' + serial_no )
                    err = 'No Invoice line found for seriral number ' + serial_no
                    error_obj.create({'name': err})

            #except:
            #    raise UserError(_('Meter Reading Import Failed!.\nPlease try again'))

            """
            for row in csv_input_file:
                serial_no = row[0].strip('"')
                colour = row[1]
                black = row[2]
                #if serial_no == 'V2294101896':
                #    print ('found it')
                #else:
                #    continue
                line_ids = line_obj.search([('x_serial_number_id', '=', serial_no)])
                if line_ids:
                    for line in line_ids:
                        if line.name == 'Black copies' and int(black) > 0:
                            #print('found Black copies serialnumber ', serial_no, line.name, line.analytic_account_id.name)
                            line.write({'x_copies_last': black})
                            #vals = {'id': line.id, 'x_copies_last': black}
                            #lines.append(vals)
                        if line.name == 'Colour copies' and int(colour) > 0:
                            #print('found Colour copies serialnumber ', serial_no, line.name, line.analytic_account_id.name)
                            line.write({'x_copies_last': colour})
                            #vals = {'id': line.id, 'x_copies_last': colour}
                            #lines.append(vals)

                else:
                    lot = self.env['stock.production.lot'].search([('name', '=', serial_no)])
                    contract_number = contract_name = ''
                    if lot:
                        contract_number = lot.x_subscription_id.name
                        contract_name = lot.x_subscription_id.partner_id.name
                        print(contract_number)

                    print('not found', serial_no)
                    err = 'No Invoice line found for serial number ' + serial_no + ', ' + contract_number + ', for Customer ' + contract_name
                    error_obj.create({'name': err})
                    continue
                # print (serial_no)


            #line_obj.write(lines)

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
