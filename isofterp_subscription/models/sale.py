from odoo import api, fields, models, _, osv
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
#from odoo import exceptions
from odoo.exceptions import ValidationError

import pandas as pd
import tempfile
import xlsxwriter
import base64


df = pd.DataFrame()

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"


    def action_spreadsheet(self):
        print("we are in action_spreadsheet")
        for rec in self:

            print('quote',rec.x_is_contract_quote)

        print('now we are here')

        file_path = tempfile.mktemp(suffix='.xlsx')
        model = []
        cash_deal = []
        rental = []
        black_charge = []
        black_vol1 = []
        color_charge = []
        color_vol1 = []

        if self.env.context.get('active_ids', False):
            sale_order_ids = self.browse(self.env.context.get('active_ids'))
            # Create a Pandas dataframe from some data.
            model.append(' ')
            black_charge.append(' ')
            black_vol1.append(' ')
            color_charge.append(' ')
            color_vol1.append(' ')
            rental.append(' ')
            cash_deal.append(' ')

            #print('40 ',len(model),model[0])

            i = 0
            for order in sale_order_ids:
                if not order.x_is_contract_quote:
                    # Only do spreadsheets for Subscription Quotes
                    self.ensure_one()
                    view_form_id = self.env.ref('isofterp_subscription.sale_subscription_form_inherit').id
                    action = {
                        'type': 'ir.actions.act_window',
                        'views': [ (view_form_id, 'form')],
                        'view_mode': 'form',
                        'name': _('Sale'),
                        'res_model': 'sale.order',
                    }
                    return action
                #Set up a row per Order
                model.append(' ')
                black_charge.append(' ')
                black_vol1.append(' ')
                color_charge.append(' ')
                color_vol1.append(' ')
                rental.append(' ')
                cash_deal.append(' ')

                for line in order.order_line:
                    if line.product_id.categ_id.name == 'main product':
                        model[i] = line.name



                        for charge in line.product_id.x_machine_charge_ids:
                            print('charge name=',charge.name)
                            if charge.name == 'Black copies':
                                black_vol1[i] = charge.copies_vol_1
                                black_charge[i] = charge.copies_price_1
                            if charge.name == 'Colour copies':
                                color_vol1[i] = charge.copies_vol_1
                                color_charge[i] = charge.copies_price_1
                    if line.product_id.name == 'Cash Deal':
                        cash_deal[i] = line.price_unit
                    if line.product_id.name == 'Finance Deal':
                        rental[i] =line.price_unit

                i = i + 1
            df = pd.DataFrame({'Model': model,
                               'Cash Deal': cash_deal,
                               'Monthly Rental Charge': rental,
                               'B & W Charge': black_charge,
                               'Avg, B&W Vol/Mth': black_vol1,
                               'Color Charge': color_charge,
                               'Avg, Color Vol/Mth': color_vol1,
                               })
            # Arrange te columns in the sequence you want them to appear in spreadsheet
            df = df[['Model', 'Cash Deal', 'Monthly Rental Charge', 'B & W Charge', 'Avg, B&W Vol/Mth', 'Color Charge',
                     'Avg, Color Vol/Mth']]
            df.style.apply(['background-color: yellow'],axis=1)

            # Create a Pandas Excel writer using XlsxWriter as the engine.
            #writer = pd.ExcelWriter("pandas_column_formats.xlsx", engine='xlsxwriter')
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')


            # Convert the dataframe to an XlsxWriter Excel object.
            df.to_excel(writer, sheet_name='Sheet1')

            # Get the xlsxwriter workbook and worksheet objects.
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']

            # Add some cell formats.
            format1 = workbook.add_format({'num_format': '#,##0.00'})
            format2 = workbook.add_format({'num_format': '0.0000'})

            # Note: It isn't possible to format any cells that already have a format such
            # as the index or headers or any cells that contain dates or datetimes.

            # Set the column width and format.
            worksheet.set_column('B:B', 50, format1)
            worksheet.set_column('C:C', 10, format1)
            worksheet.set_column('D:D', 25, format1)
            worksheet.set_column('E:E', 20, format2)
            worksheet.set_column('F:F', 20, format1)
            worksheet.set_column('G:G', 20, format2)
            worksheet.set_column('H:H', 20, format1)
            # Set the format but not the column width.
            #worksheet.set_column('C:C', None, format1)

            # Close the Pandas Excel writer and output the Excel file.
            writer.save()
            print("finished")
            workbook.close()
            with open(writer, 'rb') as r:
                xls_file = base64.b64encode(r.read())
            att_vals = {
                'name': u"{}-{}.xlsx".format('CopyType SpreadSheet', fields.Date.today()),
                'type': 'binary',
                'datas': xls_file,
            }
            attachment_id = self.env['ir.attachment'].create(att_vals)
            self.env.cr.commit()

            return attachment_id.id

    x_lot_id = fields.Many2one('stock.production.lot', 'Serial Number')
    x_sale_subscription_id = fields.Many2one('sale.subscription', 'Subscription')
    x_cash1 = fields.Float("Toner")
    x_cash2 = fields.Float("Mark up")
    x_cash3 = fields.Float("Settelment")
    x_cash4 = fields.Float("Sponsorship")
    x_cash5 = fields.Float("Salesman Profit")
    x_rental_factor = fields.Many2one("subscription.rental.factor", 'Rental Factor')
    x_is_contract_quote = fields.Boolean('Subscription Quote',help="By ticking this box it means you intend converting this Quote into a subscription")
    #x_service_type = fields.Char("Service type")
    x_service_type = fields.Char(related='x_lot_id.x_service_type_id.name')
    #x_rental_factor = fields.Selection(VALUES, string='Rental Factor')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        new_rec = super(SaleOrder, self).onchange_partner_id()
        if self._context.get('default_dlv_ids'):
            dlv_ids = self.env['res.partner'].browse(self._context.get('default_dlv_ids')).id
            self.partner_shipping_id = dlv_ids
            self.user_id = False
        return new_rec

    @api.onchange('x_lot_id')
    def onchange_x_lot_id(self, context=None):
        if not self.x_lot_id:
            return
        ana_id = self.env['account.analytic.account'].search([('name','=',self.x_lot_id.name)]).id
        if not ana_id:
            title = 'WARNING -------> ' + self.x_lot_id.product_id.name
            warning = {
                'title': title,
                'message': "There is no Analytic Account setup  for this Machine - Please do so\n if yoy want to track this product",
            }
            return {'warning': warning}
        self.analytic_account_id = ana_id
        #self.x_service_type = self.x_lot_id.x_service_type_id.name
        self.env.context = dict(self.env.context)
        self.env.context.update({'default_dlv_ids': self.x_lot_id.x_dlv_id.id})
        #print ('in onchange lot_id',self.env.context)
        self.x_sale_subscription_id = self.x_lot_id.x_subscription_id.id,
        #self.partner_id =self.x_lot_id.x_sale_subscription_id.partner_id
        self.partner_id = self.x_sale_subscription_id.partner_id
       # self.partner_id = self.x_lot_id.x_dlv_id.parent_id.id
        self.partner_shipping_id = self.x_lot_id.x_dlv_id.id
        if not self.partner_shipping_id:
            self.partner_shipping_id =  self.partner_id
        #print('and here is the delv id ',self.x_lot_id.x_dlv_id.id)
        warning = {}
        title = 'WARNING -------> ' + self.x_lot_id.product_id.name
        message = False
        message = self.x_lot_id.x_service_type_id.name
        if message:
            warning = {
                'title': title,
                'message': message,
            }
            return {'warning': warning}
        return


    def calculate_deal(self):
        #print (self.amount_untaxed)
        # Check if order line exists - if so delete them and recreate
        product_obj = self.env['product.product']
        order_line_obj = self.env['sale.order.line']
        prod_id = product_obj.search([('name', '=', 'Cash Deal')])
        print('@166',prod_id)
        if not prod_id:
             raise ValidationError("You need a Product of type Consumable called 'Cash Deal'")
        order_line_obj.search([('product_id', '=', prod_id[0].id), ('order_id', '=', self.id)]).unlink()
        amt = self.amount_untaxed + self.x_cash1 + self.x_cash2 + self.x_cash3 + self.x_cash4 + self.x_cash5
        #print ("we are in Cash Deal", prod_id.id)
        res = {
            'name': 'Cash Deal',
            'customer_lead': 0.0,
            'invoice_status': 'to invoice',
            'order_id': self.id,
            'product_id': prod_id.id,
            'product_uom_qty': 1,
            'price_unit': amt
        }
        order_line_obj.create(res)
        # create Rental order line
        res = {}
        #print ("we are in factor")
        #print ('x_rental_factor',self.x_rental_factor)

        # Changed this to keep these values in a table (contract.rental.factor)
        # can be deleted once formula has been wriiten see line 71
        # VALUES = [('0.02626', '60 months 0% escalation'),
        #           ('0.02215', '48 months 10% escalation'),
        #           ('0.02034', '48 months 15% escalation')]

        if self.x_rental_factor:
            prod_id = product_obj.search([('name', '=', 'Finance Deal')])
            if not prod_id:
                raise ValidationError("You need to create a Product of type Consumable called 'Finance Deal'")
            order_line_obj.search([('product_id', '=', prod_id[0].id), ('order_id', '=', self.id)]).unlink()
            # Now do the calculation based on the figures in the rate table
            yr = 0
            while yr < self.x_rental_factor.months / 12:
                amt = amt + amt * self.x_rental_factor.rate
                yr = yr + 1
                #print('amt=',amt,'no yrs=',yr,'no of mnth = ',self.x_rental_factor.months)
            amt = amt / self.x_rental_factor.months

            res = {
                'name': self.x_rental_factor.name,
                'order_id': self.id,
                'product_id': prod_id[0].id,
                'product_uom_qty': 1,
                'price_unit': amt
            }
            order_line_obj.create(res)

    def action_create_contract_from_quote(self):
        print('we are in action_create_contract_from_quote')
        if not self.x_is_contract_quote:
            raise ValidationError(
                "This is NOT a Subscription Quote so no Contract will be created")

        if self.env.context.get('active_ids', False):
            print('we are in action_create_contract_from_quote')
            sale_order_ids = self.browse(self.env.context.get('active_ids'))
            subscription_obj = self.env['sale.subscription']
            subscription_line_obj = self.env['sale.subscription.line']
            subscription_obj.search([('name', '=', self.name)]).unlink()
            order_line_obj = self.env['sale.order.line']
            stock_move_obj = self.env['stock.move']
            stock_move_line_obj = self.env['stock.move.line']
            for order in sale_order_ids:
                print('Found Order ',order.name,order.state)
                if order.state == 'draft':
                    print('got here')
                    raise ValidationError("You can't Create a subscription while the Quote is in Draft mode !\n You must first Confirm Sale")

                # First delete a subscription if one already exists ???
                subscription_obj.search([('x_sale_order_id', '=', order.id)]).unlink()
                # Then re-create a new subscription
                res = {
                    'partner_id': order.partner_id.id,
                    'x_sale_order_id': order.id,
                    'template_id': 1
                }
                print('res',res)
                #Now create a Contract in the custom 'create' of sale_subscription.py
                new_id = subscription_obj.create(res)
                # and link this new Contact to this Sales Order
                order.x_sale_subscription_id = new_id.id
                lines = order_line_obj.search([('order_id', '=', order.id)])
                for line in lines:
                    # create equipment  i.e category is 'component' or 'main product'
                    print('line=', line.product_id.name)
                    if line.product_id.categ_id.name in ['copies', 'charge', 'service', 'rental']:
                        if line.product_id.categ_id.name == 'copies':
                            copies = True
                        else:
                            copies = False
                        res = {
                            'name': line.name,
                            'analytic_account_id': new_id.id,
                            'uom_id': 1,
                            'product_id': line.product_id.id,
                            'x_copies_show': copies,
                            'quantity': 1,
                            'price_unit': line.price_unit,
                        }
                        print('res', res)
                        line_id = subscription_line_obj.create(res)
                        end_date = False
                    ### Create machine on this contract - look up the serial number fromthe stock_move_line
                    # which can be found via the 'origin' field which is the SO number
                    if line.product_id.categ_id.name in ['main product', 'component']:
                        if line.product_id.categ_id.name == 'main product':
                            main_prod = 1
                        move_line = stock_move_obj.search([('sale_line_id', '=', line.id)]).id
                        serial = stock_move_line_obj.search([('move_id', '=', move_line)]).lot_id.id
                        if not serial:
                            delivery_note = self.env['stock.picking'].search([('sale_id', '=', order.id)]).name
                            msg = "You can't Create a subscription until Serial Numbers have been allocated by Stores !\n"
                            msg = msg + "Please ask Stores to confirm Delivery Note number " + delivery_note
                            raise ValidationError(msg)
                        #print('found main prod',order.name,serial)
                        new_id.x_machine_ids = [(4, serial,0)]
                        #new_id.x_machine_ids = [(6, 0, [serial])]
                        # Now create Subscription lines from pre loaded charges on this product
                        for rec in line.product_id.x_machine_charge_ids:
                            show = False
                            if rec.product_id.categ_id.name == 'copies':
                                show = True
                                res = {
                                    'name': " Tier One",
                                    'uom_id': 1,
                                    'product_id': rec.product_id.id,
                                    'quantity': 0,
                                    'price_unit': rec.copies_price_1,
                                    'analytic_account_id': new_id.id,
                                    'x_copies_show': show,
                                    'x_product_id': line.product_id,
                                    'x_serial_number_id': serial,
                                    'x_copies_minimum': rec.minimum_charge,
                                    'x_copies_free': rec.copies_free,
                                    'x_copies_vol_1': rec.copies_vol_1,
                                    'x_copies_price_1': rec.copies_price_1,
                                    'x_copies_vol_2': rec.copies_vol_2,
                                    'x_copies_price_2': rec.copies_price_2,
                                    'x_copies_vol_3': rec.copies_vol_2,
                                    'x_copies_price_3': rec.copies_price_3,
                                }
                                line_id = subscription_line_obj.create(res)
                            else:
                                res = {
                                    'name': rec.name,
                                    'uom_id': 1,
                                    'product_id': rec.product_id.id,
                                    'quantity': rec.qty,
                                    'price_unit': rec.price,
                                    'analytic_account_id': new_id.id,
                                    'x_copies_show': show,
                                    'x_product_id': line.product_id,
                                    'x_serial_number_id': serial,

                                }
                                line_id = subscription_line_obj.create(res)
                    if line.product_id.name == 'Finance Deal':
                        print('Finance deal',line.product_id.name,line.product_id.categ_id.name)
                        factor_odj = self.env['subscription.rental.factor']
                        factor_line = factor_odj.search([('name', '=', line.name)])
                        mnths = factor_line.months - 1
                        end_date = datetime.today() + relativedelta(months=mnths)
                        res = {
                            'name': line.name,
                            'analytic_account_id': new_id.id,
                            'uom_id': 1,
                            'product_id': line.product_id.id,
                            'x_copies_show': False,
                            'quantity': -1,
                            'price_unit': line.price_unit,
                            'x_end_date1': end_date,
                            'x_start_date1_billable': False,  # Bank will do the billing
                        }
                        line_id = subscription_line_obj.create(res)
                        # Now create a billing line to start billing customer once Bank billing has stopped
                        start_date = datetime.today() + relativedelta(months=mnths + 1)
                        line.price_unit += line.price_unit * factor_line.escalation / 100
                        res = {
                            'name': line.name,
                            'analytic_account_id': new_id.id,
                            'uom_id': 1,
                            'product_id': line.product_id.id,
                            'x_copies_show': False,
                            'quantity': 1,
                            'price_unit': line.price_unit,
                            'x_start_date1': start_date,
                            'x_start_date1_billable': True,  # Start billing next month after bank billing stops

                        }
                        line_id = subscription_line_obj.create(res)

    def create_subscription_from_quote_OLD(self):
        # if self.state == 'draft':
        #    #raise Warning('Warning message')
        #    raise ValidationError("You can't Create a subscription while the Quote is in Draft mode !\n You must first Confirm Sale")

        subscription_obj = self.env['sale.subscription']
        subscription_obj.search([('name', '=', order.name)]).unlink()
        subscription_line_obj = self.env['sale.subscription.line']
        quote_id = self.id
        order_line_obj = self.env['sale.order.line']
        lines = order_line_obj.search([('order_id', '=', quote_id)])
        stock_move_line_obj = self.env['stock.move.line']

        # first create a new subscription
        res = {
            #'name': self.name,
            'partner_id': self.partner_id.id,
            #'recurring_invoices': True,
            #'create_invoice_visibility': True,
            #'journal_id': 1,
            'x_sale_order_id': self.id
        }

        new_id = subscription_obj.create(res)
        self.x_sale_subscription_id = new_id.id

        for line in lines:
            # create equipment  i.e category is 'component' or 'main product'
            # dont know how to do this because of the serial number issue
            print('line=',line)
            if line.product_id.categ_id.name in ['copies','charge','service','rental']:
                copies = False
                if line.product_id.categ_id.name == 'copies':
                    copies = True
                res = {
                    'name': line.name,
                    'analytic_account_id': new_id.id,
                    'uom_id': 1,
                    'product_id': line.product_id.id,
                    'x_copies_show': copies,
                    'quantity': 1,
                    'price_unit': line.price_unit,
                }
                print('res',res)
                line_id = subscription_line_obj.create(res)
                end_date = False
            ### Create machine on this contract - look up the serial number fromthe stock_move_line
            # which can be found via the 'origin' field which is the SO number
            if line.product_id.categ_id.name in ['main product','component']:
                if line.product_id.categ_id.name == 'main product':
                    main_prod = 1
                serial = stock_move_line_obj.search([('origin','=',self.name)]).lot_id.id
                new_id.x_machine_ids =  [(6, 0, [serial])]
                # Now create Subscription lines from pre loaded charges onthis product
                for rec in line.product_id.x_machine_charge_ids:
                    show = False
                    if rec.product_id.categ_id.name == 'copies':
                        show = True
                        res = {
                            'name': " Tier One",
                            'uom_id': 1,
                            'product_id': rec.product_id.id,
                            'quantity': 0,
                            'price_unit': rec.copies_price_1,
                            'analytic_account_id': new_id.id,
                            'x_copies_show': show,
                            'x_product_id': line.product_id,
                            'x_serial_number_id': serial,
                            'x_copies_minimum': rec.minimum_charge,
                            'x_copies_free': rec.copies_free,
                            'x_copies_vol_1': rec.copies_vol_1,
                            'x_copies_price_1': rec.copies_price_1,
                            'x_copies_vol_2': rec.copies_vol_2,
                            'x_copies_price_2': rec.copies_price_2,
                            'x_copies_vol_3': rec.copies_vol_2,
                            'x_copies_price_3': rec.copies_price_3,
                        }
                        line_id = subscription_line_obj.create(res)
                    else:
                        res = {
                            'name': rec.name,
                            'uom_id': 1,
                            'product_id': rec.product_id.id,
                            'quantity': rec.qty,
                            'price_unit': rec.price,
                            'analytic_account_id': new_id.id,
                            'x_copies_show': show,
                            'x_product_id': line.product_id,
                            'x_serial_number_id': serial,

                        }
                        line_id = subscription_line_obj.create(res)
            if line.product_id.categ_id.name == 'finance deal':
                print (line.product_id.categ_id.name)

                factor_odj=self.env['subscription.rental.factor']
                factor_line = factor_odj.search([('name','=', line.name)])
                mnths = factor_line.months - 1
                end_date = datetime.today()+relativedelta(months=mnths)
                res =  {
                            'name': line.name,
                            'analytic_account_id': new_id.id,
                            'uom_id': 1,
                            'product_id': line.product_id.id,
                            'x_copies_show': False,
                            'quantity': 1,
                            'price_unit': line.price_unit,
                            'x_end_date1': end_date,
                            'x_start_date1_billable': False,           #Bank will do the billing
                        }
                line_id = subscription_line_obj.create(res)
                # Now create a billing line to start billing customer once Bank billing has stopped
                start_date = datetime.today() + relativedelta(months=mnths+1)
                line.price_unit += line.price_unit * factor_line.escalation / 100
                res = {
                    'name': line.name,
                    'analytic_account_id': new_id.id,
                    'uom_id': 1,
                    'product_id': line.product_id.id,
                    'x_copies_show': False,
                    'quantity': 1,
                    'price_unit': line.price_unit,
                    'x_start_date1': start_date,
                    'x_start_date1_billable': True,  # Start billing next month after bank billing stops

                }
                line_id = subscription_line_obj.create(res)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_component_ids = fields.Many2many(related='product_id.x_optional_component_ids')

    @api.onchange('product_id')
    def onchange_product_id(self, context=None):
        if not self.product_id :
            return
        if self.order_id.x_is_contract_quote and len(self.product_id.x_machine_charge_ids) == 0:
            warning = {}
            title = 'WARNING -------> ' + self.product_id.name
            message = False
            message = "This Product has no Charges loaded. Go to Products and add Charges i.e Copy charges etc"
            if message:
                warning = {
                    'title': title,
                    'message': message,
                }
                return {'warning': warning}

    # def add_component(self):
    #     list = []
    #     print(self.product_id.x_optional_component_ids)
    #     #self.sale_order_option_ids = [(4,975)]
    #     #print('sales opt',self.sale_order_option_ids)
    #     for id in self.x_component_ids:
    #         list.append(id.id)
    #     print(list)
    #     return {
    #         'name': self.name,
    #         'view_type': 'form',
    #         'view_mode': 'many2many',
    #         'res_model': 'product.template',  # this is the which form i want when i clcik button
    #         'views': [(1685, 'tree')],
    #         'type': 'ir.actions.act_window',
    #         'target': 'current:',
    #         'domain': [('id','=', list)],
    #         'context':self.env.context,
    #     }

        # rec = super(SaleOrderLine,self).create(vals_list)
        #
        # return rec









    



