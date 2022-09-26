# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import base64
import tempfile

try:
    import xlsxwriter
except ImportError:
    raise ValidationError("Cannot import xlsxwriter")
    print("Cannot import xlsxwriter")
    xlsxwriter = False


class AddHocIncrease(models.TransientModel):
    _name = 'addhoc.increase.wizard'
    _description = 'Addhock Increases'

    amt_start = fields.Float('Rand amount to start')
    amt_end = fields.Float('Rand amount to end')
    copy_chrg_1 = fields.Selection( selection=[('no', 'No'),('yes', 'Yes')],default='no',string='Update copy charge 1')
    copy_chrg_2 = fields.Selection( selection=[('no', 'No'),('yes', 'Yes')],default='no',string='Update copy charge 2')
    copy_chrg_3 = fields.Selection( selection=[('no', 'No'),('yes', 'Yes')],default='no',string='Update copy charge 3')
    service_chrg = fields.Selection( selection=[('no', 'No'),('yes', 'Yes')],default='no',string='Update service amount')
    chrg_type = fields.Selection(selection=[('percent', 'Percent'),('amt', 'Amount'),],string='Increase by')
    amount = fields.Float('Amount')

    def _check_range(self,value):
        if self.amt_start <= value <= self.amt_end and round(value, 4) == value:
            return True
        return False

    def _calculate_increase(self,value):

        if self.chrg_type == 'percent':
            after_value = value + (value * self.amount / 100)
            print (value , after_value)
            return after_value
        if self.chrg_type == 'amt':
            return value + self.amount


    def run_increase_update(self):

        lines = self.env['sale.subscription.line'].search([ ('name','in',['Black copies','Colour copies','Monthly Service',]),('analytic_account_id.x_add_hoc_increase','=','yes') ])
        print('in lines')
        for line in lines:
            if line.name == 'Black copies' or line.name == 'Colour copies':
                print('we are here @ 51 add_hoc_incease')
                if self.copy_chrg_1 == 'yes' and self._check_range(line.x_copies_price_1):
                    line.x_copies_price_1 = self._calculate_increase(line.x_copies_price_1)
                if self.copy_chrg_2 == 'yes' and self.check_range(line.x_copies_price_2):
                    line.x_copies_price_2 = self._calculate_increase(line.x_copies_price_2)
                if self.copy_chrg_3 == 'yes' and self.check_range(line.x_copies_price_3):
                    line.x_copies_price_3 = self._calculate_increase(line.x_copies_price_3)
                continue

            if line.name == 'Monthly Service':
                if self.service_chrg == 'yes' and self._check_range(line.price_unit):
                    line.price_unit = self._calculate_increase(line.price_unit)

        return self.generate_xlsx_report()


    def generate_xlsx_report(self):


        print_rows = []
        file_path = tempfile.mktemp(suffix='.xlsx')
        workbook = xlsxwriter.Workbook(file_path)
        sheet = workbook.add_worksheet('My Report')

        row = 1
        col = 0
        print_rows.append([['Before Value', 2],
                           ['After Value ', 4],

                           ])

        for a, b in print_rows:
            sheet.write(row, col, a[1],)
            sheet.write(row, col + 1, b[1], )
            row += 1

            # for a, b, c, d, e, f, g, h, j, k, i in print_rows:
            #     sheet.write(0, 0, a[0], hstyle)
            #     sheet.write(0, 1, b[0], hstyle)
            #     sheet.write(0, 2, c[0], hstyle)
            #     sheet.write(0, 3, d[0], hstyle)
            #     sheet.write(0, 4, e[0], hstyle)
            #     sheet.write(0, 5, f[0], hstyle)
            #     sheet.write(0, 6, g[0], hstyle)
            #     sheet.write(0, 7, h[0], hstyle)
            #     sheet.write(0, 8, j[0], hstyle)
            #     sheet.write(0, 9, k[0], hstyle)
            #     sheet.write(0, 10, i[0], hstyle)
        workbook.close()
        with open(file_path, 'rb') as r:
            xls_file = base64.b64encode(r.read())
        att_vals = {
            'name':  u"{}-{}.xlsx".format('Report name roly', fields.Date.today()),
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
        print('in report', action)
        return action

# class AddHocAuditReport(models.Model):
#     _name = "Add Hoc Audit Report"
#
#     name = fields.Char('Transaction')

