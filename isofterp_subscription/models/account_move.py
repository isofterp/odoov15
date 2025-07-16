import base64
import io
import tempfile

import werkzeug
import werkzeug.exceptions
from odoo import api, fields, models, _, osv, http
import logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from io import BytesIO
from odoo.exceptions import ValidationError
import xlsxwriter
from odoo.http import content_disposition, request
from urllib.parse import urlencode

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    x_no_charge = fields.Boolean("Tick here if you want to create a No Charge Invoice", help="Tick if you want a No-Charge Sale")
    x_lot_id = fields.Many2one('stock.production.lot', 'Serial Number')
    x_partner_dlv_street = fields.Char(related='partner_shipping_id.street', string='Street')
    x_partner_dlv_street2 = fields.Char(related='partner_shipping_id.street2', string='')
    x_partner_dlv_email = fields.Char(related='partner_shipping_id.email', string='')
    x_partner_dlv_phone = fields.Char(related='partner_shipping_id.phone', string='')
    x_partner_dlv_mobile = fields.Char(related='partner_shipping_id.mobile', string='')
    x_product_name = fields.Char(related='x_lot_id.product_id.product_tmpl_id.name')
    x_copies_black = fields.Char(string='Meter Reading (B&W)')
    x_copies_color = fields.Char(string='Meter Reading (Color)')
    x_account_number = fields.Char(related='partner_id.x_account_number', string='Account Number', store=True)
    x_main_partner = fields.Many2one('res.partner', readonly=True, tracking=True,
                                 states={'draft': [('readonly', False)]},
                                 check_company=True,
                                 string='Main Partner', change_default=True, ondelete='restrict')


    def back_date_invoices(self):

        dt_last = datetime(2023,12,22)
        invoices = self.env['account.move'].search([('move_type','=','out_invoice'),
                                                    ('date','<=', dt_last),
                                                    ('state', '=', 'draft')])
        cur_date = date.today()
        past_date= cur_date - relativedelta(years=1)
        logging.warning("Current Date and past year %s %s", cur_date, past_date)

        for invoice in invoices:
            # invoice.invoice_date = invoice.date
            # invoice.invoice_date_due = invoice.date

            logging.warning("last year - Name Date %s %s %s %s", invoice.name, invoice.invoice_date, invoice.invoice_date_due,invoice.date)
            invoice._post()

    def action_export_payment_auth(self):
        logging.warning("---------we are in action_export_payment_auth")
        #self.ensure_one()
        file_path = tempfile.mktemp(suffix='.xlsx')
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet(u"{}.xlsx".format(fields.Date.today()))

        row = 0
        report_total_excl = 0
        report_total = 0
        report_total_vat = 0
        report_total_to_pay = 0
        report_line_total_pay = 0

        total_list = []
        report_header = ['Vendor Bill Payment Authorization Report']
        header_style = workbook.add_format({'bold': True, 'border': 1})
        detail_style = workbook.add_format({'border': 1})
        currency = workbook.add_format({'num_format': 'R#,##0.00', 'border': 1})
        rep_tot = workbook.add_format({'bold': True,'num_format': 'R#,##0.00', 'border': 1})
        worksheet.set_column(0, 0, 40)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 2, 20)
        worksheet.set_column(3, 3, 20)
        worksheet.set_column(4, 4, 20)
        worksheet.set_column(5, 5, 20)
        worksheet.set_column(6, 6, 20)
        worksheet.set_column(7, 7, 20)

        for counter, column in enumerate(report_header):
            value = column
            worksheet.write(row, counter, value, header_style)
        worksheet.write(row,3,'Date',header_style)
        worksheet.write(row,4,str(date.today()),detail_style)
        row +=1

        report_sub_header = ['Vendor', 'Invoice Number', 'Invoice Reference', 'Invoice Date', 'Amount (Excl)', 'VAT', 'Amount (Incl)','Amount to Pay']
        for counter, column in enumerate(report_sub_header):
            value = column
            worksheet.write(row, counter, value, header_style)
        row +=1

        # Get all the details for the report
        if self.env.context.get('active_ids', False):
            invoices = self.browse(self.env.context.get('active_ids'))

        for invoice in invoices:
            invoice_list = []
            invoice_list.append(invoice.partner_id.name)
            invoice_list.append(invoice.name)
            invoice_list.append(invoice.invoice_origin or 'N/A')
            invoice_list.append(str(invoice.invoice_date))
            invoice_list.append(invoice.amount_untaxed)
            invoice_list.append(invoice.amount_tax)
            invoice_list.append(invoice.amount_total)
            invoice_list.append(invoice.amount_residual)
            for counter, column in enumerate(invoice_list):
                value = column
                logging.warning("Value is %s and Type %s", value, type(value))
                if isinstance(value, float):
                    worksheet.write(row, counter, value, currency)
                else:
                    worksheet.write(row, counter, value, detail_style)
            row +=1
            report_total_excl += invoice.amount_untaxed
            report_total_vat += invoice.amount_tax
            report_total += invoice.amount_total
            report_total_to_pay += invoice.amount_residual


        worksheet.write(row, 4, report_total_excl, rep_tot)
        worksheet.write(row, 5, report_total_vat, rep_tot)
        worksheet.write(row, 6, report_total, rep_tot)
        worksheet.write(row, 7, report_total_to_pay, rep_tot)

        workbook.close()
        with open(file_path, 'rb') as r:
            xls_file = base64.b64encode(r.read())
        att_vals = {
            'name': u"{}-{}.xlsx".format("Vendor Bill Payment Authorization", format(fields.Date.today())),
            'type': 'binary',
            'datas': xls_file,
        }
        attachment_id = self.env['ir.attachment'].create(att_vals)
        self.env.cr.commit()
        action = {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id, ),
            'target': 'self',
        }
        return action



        # invoice_list = []
        # if self.env.context.get('active_ids', False):
        #     invoices = self.browse(self.env.context.get('active_ids'))
        #
        # logging.warning(type(invoices))
        # for invoice in invoices:
        #     invoice_list.append(invoice.id)
        #
        # params = {'list_param': invoice_list}
        # logging.warning("Invoices are %s", params)
        # encoded_params = urlencode(params, doseq=True)
        # base_url = "/invoicing/excel_report/VendorBillPreAuth/"
        #
        # url_with_params = f"{base_url}?{encoded_params}"
        # logging.warning("URL PArams %s", url_with_params)
        # return {
        #     'type': 'ir.actions.act_url',
        #
        #     'url': url_with_params,
        #     'target': 'new',
        # }
        # Prepare your data in a list of lists or a similar structure
        # if self.env.context.get('active_ids', False):
        #     logging.warning("ACTIVE IDS %s", self.env.context.get('active_ids', False))
        #     invoices = self.browse(self.env.context.get('active_ids'))
        #
        #     i = 0
        #     for invoice in invoices:
        #         if invoice.state != 'posted':
        #             raise UserError(_('All of some invoices have not been validated.'))
        #
        # response = request.make_response(
        #     None,
        #     headers=[
        #         ('Content-Type', 'application/vnd.ms-excel'),
        #         ('Content-Disposition', content_disposition('Invoice_report' + '.xlsx'))
        #     ]
        # )
        # output = io.BytesIO()
        # workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # header_style = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        # sheet = workbook.add_worksheet("invoices")
        # sheet.write(1, 0, 'No.', header_style)
        # sheet.write(1, 1, 'Invoice Reference', header_style)
        # sheet.write(1, 2, 'Customer', header_style)
        # workbook.close()
        # output.seek(0)
        # response.stream.write(output.read())
        # output.close()
        # return response

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    x_account_number = fields.Char(related='partner_id.x_account_number', string='Account Number', store=True)








    




