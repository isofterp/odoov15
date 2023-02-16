# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import base64
import tempfile
from datetime import datetime, time, date

try:
    import xlsxwriter
except ImportError:
    raise ValidationError("Cannot import xlsxwriter")
    #print("Cannot import xlsxwriter")
    xlsxwriter = False


class AddHocIncrease(models.TransientModel):
    _name = 'addhoc.increase.wizard'
    _description = 'Addhock Increases'

    current_user = fields.Char('Current User',default=lambda self: self.env.user.name)
    yes_to_backup = fields.Char("Have you made a Backup of the Database? If so, enter 'Yes' in this field.")
    min_amount = fields.Float('Minimum amount', default=1,help='Only records with a value between the minimum and maximum will be updated.')
    max_amount = fields.Float('Maximum amount',default=9999999, help='Only records with a value between the minimum and maximum will be updated.')
    start_date = fields.Date('Start Date', help='Only records with a start date on or after this date will be updated. Leave blank to update all records.')
    end_date = fields.Date('End Date', help='Only records with an end date on or before this date will be updated. Leave blank to update all records.')
    copy_chrg_1 = fields.Selection( selection=[('no', 'No'),('yes', 'Yes')],default='no',string='Update Copy charge 1')
    copy_chrg_2 = fields.Selection( selection=[('no', 'No'),('yes', 'Yes')],default='no',string='Update Copy charge 2')
    copy_chrg_3 = fields.Selection( selection=[('no', 'No'),('yes', 'Yes')],default='no',string='Update Copy charge 3')
    service_chrg = fields.Selection( selection=[('no', 'No'),('yes', 'Yes')],default='no',string='Update Service amount')
    rental_chrg = fields.Selection( selection=[('no', 'No'),('yes', 'Yes')],default='no',string='Update Rental amount')
    chrg_type = fields.Selection(selection=[('Percent', 'Percent'),('Amount', 'Amount')],string='Increase by')
    #chrg_type = fields.Selection(selection=[('percent', 'Percent'),('amt', 'Amount')],string='Increase by')
    amount = fields.Float('Amount')

    print_rows = []

    def _check_range(self,value):
        """Check if the value is in the range of min and max amount and range of the start and end dates"""
        if self.min_amount <= value <= self.max_amount and round(value, 4) == value:  # value for copies is rounded to 4 decimal places
            if self.start_date and self.end_date:
                if self.start_date <= line.start_date <= self.end_date:
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False

    def _calculate_increase(self, line,old_value):
        if self.chrg_type == 'Percent':
            after_value = old_value + (old_value * self.amount / 100)
        else:
            after_value = old_value + self.amount
        """append the values to the print_rows list to be used in the xlsx report"""
        self.print_rows.append([line.analytic_account_id.name,
                                line.analytic_account_id.partner_id.name,
                                line.name, line.x_serial_number_id.product_id.name,line.x_serial_number_id.name,
                                old_value,after_value,after_value - old_value])
        return after_value

    def run_increase_update(self):
        """Check if the user has made a backup of the database"""
        if self.yes_to_backup != 'Yes':
            raise ValidationError("You must make a backup of the database before running this wizard. Type 'Yes' in the 'Have you made a Backup of the Database?' field to continue.")
        lines = self.env['sale.subscription.line'].search([ ('name','in',['Black copies',
                                                                          'Colour copies',
                                                                          'Monthly Service',
                                                                          'Monthly Rental']
                                                             ),
                                                            ('analytic_account_id.x_add_hoc_increase','=','yes') ])

        for line in lines:
            if line.name == 'Black copies' or line.name == 'Colour copies':
                if self.copy_chrg_1 == 'yes' and self._check_range(line.x_copies_price_1):
                    line.x_copies_price_1 = self._calculate_increase(line,line.x_copies_price_1)
                if self.copy_chrg_2 == 'yes' and self.check_range(line.x_copies_price_2):
                    line.x_copies_price_2 = self._calculate_increase(line,line.x_copies_price_2)
                if self.copy_chrg_3 == 'yes' and self.check_range(line.x_copies_price_3):
                    line.x_copies_price_3 = self._calculate_increase(line,line.x_copies_price_3)
            if line.name == 'Monthly Service':
                if self.service_chrg == 'yes' and self._check_range(line.price_unit):
                    line.price_unit = self._calculate_increase(line,line.price_unit)
            if line.name == 'Monthly Rental':
                if self.rental_chrg == 'yes' and self._check_range(line.price_unit):
                    line.price_unit = self._calculate_increase(line,line.price_unit)

        self.yes_to_backup = 'No'
        return self.generate_xlsx_report(self.print_rows)

    def generate_xlsx_report(self,print_rows):
        file_path = tempfile.mktemp(suffix='.xlsx')
        workbook = xlsxwriter.Workbook(file_path)
        sheet = workbook.add_worksheet('My Report')
        number_format = workbook.add_format({'num_format': '###,###.0000'})


        sheet.set_column('A:A', 12)
        sheet.set_column('B:B', 40)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 25)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:H', 10,number_format)


        row = 1
        col = 0

        """write first header row"""
        sheet.write(0, col, 'Add Hock Increase')
        col += 1
        sheet.write(0, col, 'Run by     ' + self.current_user)
        col += 1
        sheet.write(0, col, 'Date')
        col += 1
        sheet.write(0, col, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        col += 1
        sheet.write(0, col, 'Increase by')
        col += 1
        sheet.write(0, col, self.amount)
        col += 1
        sheet.write(0, col, self.chrg_type)
        col = 0
        row += 1
        """write second header row"""

        col = 0
        sheet.write(row, col, 'Contract Number' )
        col += 1
        sheet.write(row, col, 'Customer')
        col += 1
        sheet.write(row, col, 'Type')
        col += 1
        sheet.write(row, col, 'Product')
        col += 1
        sheet.write(row, col, 'Serial Number')
        col += 1
        sheet.write(row, col, 'Before ')
        col += 1
        sheet.write(row, col, 'After ')
        col += 1
        sheet.write(row, col, 'Increase ')

        row += 1

        """write the values of the report"""
        col=0

        for a, b, c, d, e, f, g, h, in print_rows:
            sheet.write(row, col, a,)
            col += 1
            sheet.write(row, col, b, )
            col += 1
            sheet.write(row, col, c, )
            col += 1
            sheet.write(row, col, d, )
            col += 1
            sheet.write(row, col, e, )
            col += 1
            sheet.write(row, col, f,)
            col += 1
            sheet.write(row, col, g, )
            col += 1
            sheet.write(row, col, h, )
            row += 1
            col= 0


        workbook.close()
        with open(file_path, 'rb') as r:
            xls_file = base64.b64encode(r.read())
        att_vals = {
            'name':  u"{}-{}.xlsx".format('Add Hock report ', fields.Date.today()),
            'type': 'binary',
            'datas': xls_file,
        }

        attachment_id = self.env['ir.attachment'].create(att_vals)
        self.env.cr.commit()

        action = {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id,),
            'target': 'self',
        }
        return action

    #return {'type': 'ir.actions.act_window_close'}

# class AddHocAuditReport(models.Model):
#     _name = "Add Hoc Audit Report"
#
#     name = fields.Char('Transaction')

