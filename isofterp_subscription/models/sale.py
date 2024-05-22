from odoo import api, fields, models, _, osv
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
# from odoo import exceptions
from odoo.exceptions import ValidationError, UserError
from odoo.tools.misc import groupby
from odoo.tools import float_compare, float_round, float_is_zero


import pandas as pd
import tempfile
import xlsxwriter
import base64

df = pd.DataFrame()

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _saleorder_create_analytic_account_prepare_values(self):
        """
         Prepare values to create analytic account
        :return: list of values
        """
        return {
            'name': self.team_id.name,
            'group_id': 8,
            'company_id': self.company_id.id,
        }

    def _analytic_account_generation(self):
        """ Generate analytic account for the so , and link it.
            :return a mapping with the so id and its linked analytic account
            :rtype dict
        """
        result = {}
        values = self._saleorder_create_analytic_account_prepare_values()
        analytic_account = self.env['account.analytic.account'].sudo().create(values)
        self.write({'analytic_account_id': analytic_account.id})
        result[self.id] = analytic_account
        return result

    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        if not self.multi_address_delivery:
            for line in self.order_line:
                line.delivery_addr_id = self.partner_shipping_id.id
        if not self.analytic_account_id:
            self._analytic_account_generation()
        return res

    def _prepare_invoice(self):
        _logger.warning("*********** Calling line at 57")
        res = super(SaleOrder, self)._prepare_invoice()
        for rec in self:
            if rec.x_sale_subscription_id:
                res['ref'] = "Rental Contract number " + rec.x_sale_subscription_id.name
            res['x_partner_dlv_street'] = rec.x_partner_dlv_street
            res['x_partner_dlv_street2'] = rec.x_partner_dlv_street2
            res['x_partner_dlv_email'] = rec.x_partner_dlv_email
            res['x_partner_dlv_phone'] = rec.x_partner_dlv_phone
            res['x_partner_dlv_mobile'] = rec.x_partner_dlv_mobile
            res['x_product_name'] = rec.x_product_name
            res['x_copies_black'] = rec.x_copies_black
            res['x_copies_color'] = rec.x_copies_color
        # res['x_no_charge'] = self.x_no_charge
        return res

    def action_spreadsheet(self):
        print("we are in action_spreadsheet")
        for rec in self:
            print('quote', rec.x_is_contract_quote)

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
            sale_order_id = self.browse(self.env.context.get('active_ids'))
            # Create a Pandas dataframe from some data.
            model.append(' ')
            black_charge.append(' ')
            black_vol1.append(' ')
            color_charge.append(' ')
            color_vol1.append(' ')
            rental.append(' ')
            cash_deal.append(' ')

            # print('40 ',len(model),model[0])

            i = 0
            for order in sale_order_id:
                if not order.x_is_contract_quote:
                    # Only do spreadsheets for Subscription Quotes
                    self.ensure_one()
                    view_form_id = self.env.ref('isofterp_subscription.sale_subscription_form_inherit').id
                    action = {
                        'type': 'ir.actions.act_window',
                        'views': [(view_form_id, 'form')],
                        'view_mode': 'form',
                        'name': _('Sale'),
                        'res_model': 'sale.order',
                    }
                    return action
                # Set up a row per Order
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
                            #print('charge name=', charge.name)
                            if charge.name == 'Black copies':
                                black_vol1[i] = charge.copies_vol_1
                                black_charge[i] = charge.copies_price_1
                            if charge.name == 'Colour copies':
                                color_vol1[i] = charge.copies_vol_1
                                color_charge[i] = charge.copies_price_1
                    if line.product_id.name == 'Cash Deal':
                        cash_deal[i] = line.price_unit
                    if line.product_id.name == 'Finance Deal':
                        rental[i] = line.price_unit

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
            df.style.apply(['background-color: yellow'], axis=1)

            # Create a Pandas Excel writer using XlsxWriter as the engine.
            # writer = pd.ExcelWriter("pandas_column_formats.xlsx", engine='xlsxwriter')
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
            # worksheet.set_column('C:C', None, format1)

            # Close the Pandas Excel writer and output the Excel file.
            writer.save()
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
    x_is_billable = fields.Boolean(related='x_lot_id.x_service_type_id.billable')
    x_sale_subscription_id = fields.Many2one('sale.subscription', 'Subscription')
    x_finance_rental = fields.Float("Rental", digits=(6, 2))
    x_finance_factor = fields.Float("Factor Used", digits=(3, 5))
    x_finance_months = fields.Selection([
        ('12', '12 Mnths'),
        ('24', '24 Mnths'),
        ('36', '36 Mnths'),
        ('48', '48 Mnths'),
        ('60', '60 Mnths'),
        ('72', '72 Mnths'),
    ], string="Term")
    x_finance_capital = fields.Float("Capital")
    x_finance_cost = fields.Float("Cost", digits=(6, 2))
    x_finance_settlement = fields.Float("Settlement", digits=(6, 2))
    x_finance_escalation = fields.Selection([('0', '0%'),
                                             ('5', '5%'),
                                             ('10', '10%'),
                                             ('15', '15%'), ],
                                            string="Escalation %", default='0')
    x_finance_profit = fields.Float("Profit")
    x_rental_factor = fields.Many2one("subscription.rental.factor", 'Rental Factor')
    x_is_contract_quote = fields.Boolean('Subscription Quote',
                                         help="By ticking this box it means you intend converting this Quote into a subscription")
    x_service_type = fields.Char(related='x_lot_id.x_service_type_id.name')
    x_component_ids = fields.Many2many(related='x_lot_id.product_id.x_optional_component_ids')
    x_no_charge = fields.Boolean("Tick here if you want to create a No Charge Invoice",
                                 help="Tick if you want a No-Charge Sale")
    x_partner_dlv_street = fields.Char(related='partner_shipping_id.street', string='Street')
    x_partner_dlv_street2 = fields.Char(related='partner_shipping_id.street2', string='')
    x_partner_dlv_email = fields.Char(related='partner_shipping_id.email', string='')
    x_partner_dlv_phone = fields.Char(related='partner_shipping_id.phone', string='')
    x_partner_dlv_mobile = fields.Char(related='partner_shipping_id.mobile', string='')
    x_product_name = fields.Char(related='x_lot_id.product_id.product_tmpl_id.name')
    x_copies_black = fields.Char(string='Meter Reading (B&W)')
    x_copies_color = fields.Char(string='Meter Reading (Color)')
    x_account_number = fields.Char(related='partner_id.x_account_number', string='Account Number')


    # @api.constrains('x_finance_rental', 'x_finance_factor', 'x_finance_settlement', 'x_finance_cost')
    # def _check_values(self):
    #     for rec in self:
    #         if rec.x_finance_rental <= 0 and rec.x_is_contract_quote:
    #             raise ValidationError('Please enter a valid value for Rental')
    #         if rec.x_finance_factor <= 0 and rec.x_is_contract_quote:
    #             raise ValidationError('Please enter a valid value for Factor')
    #         if not rec.x_finance_months and rec.x_is_contract_quote:
    #             raise ValidationError('Please enter a valid value for Months')

    @api.onchange('x_finance_rental', 'x_finance_factor', 'x_finance_settlement', 'x_finance_cost')
    def onchange_finance_deal(self):
        if self.x_finance_rental and self.x_finance_factor:
            self.x_finance_capital = self.x_finance_rental / self.x_finance_factor
            self.x_finance_profit = self.x_finance_capital - self.x_finance_settlement - self.x_finance_cost

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
        if self.order_line:
            for rec in self.order_line:
                rec.unlink()
                return
        self.env.context = dict(self.env.context)
        self.env.context.update({'default_dlv_ids': self.x_lot_id.x_dlv_id.id})
        ana_id = self.env['account.analytic.account'].search([('name', '=', self.x_lot_id.name)]).id
        if not ana_id:
            title = 'WARNING -------> ' + self.x_lot_id.product_id.name
            warning = {
                'title': title,
                'message': "There is no Analytic Account setup  for this Machine - Please do so\n if yoy want to track this product",
            }
            return {'warning': warning}
        self.analytic_account_id = ana_id
        # self.x_service_type = self.x_lot_id.x_service_type_id.name

        # print ('in onchange lot_id',self.env.context)
        self.x_sale_subscription_id = self.x_lot_id.x_subscription_id.id,
        self.partner_id = self.x_sale_subscription_id.partner_id
        self.partner_shipping_id = self.x_lot_id.x_dlv_id.id
        if not self.partner_shipping_id:
            self.partner_shipping_id = self.partner_id
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

    """This is called from the 'Done' button on the form once finance deal has been entered"""

    def update_deal(self):
        return
        # prod_id = self.env['product.product'].search([('name', '=', 'Finance Deal')])
        # if not prod_id:
        #     raise ValidationError("You need to create a Product of type Consumable called 'Finance Deal'")
        # self.env['sale.order.line'].search([('product_id', '=', prod_id.id), ('order_id', '=', self.id)]).unlink()
        # """Now create a new Rental line using the values from the finance deal"""
        # res = {
        #     'name': 'Monthly Rental',
        #     'order_id': self.id,
        #     'product_id': prod_id.id,
        #     'product_uom_qty': 1,
        #     'price_unit': self.x_finance_rental
        # }
        # self.env['sale.order.line'].create(res)

    def action_create_contract_from_quote(self):
        if self.env.context.get('active_ids', False):
            analytic_obj = self.env['account.analytic.account']
            sale_order_id = self.browse(self.env.context.get('active_ids'))
            subscription_obj = self.env['sale.subscription']
            subscription_line_obj = self.env['sale.subscription.line']
            subscription_obj.search([('name', '=', self.name)]).unlink()
            order_line_obj = self.env['sale.order.line']
            stock_move_obj = self.env['stock.move']
            stock_move_line_obj = self.env['stock.move.line']
            stock_production_lot_obj = self.env['stock.production.lot']
            # product_template_obj = self.env['product.template']
            for order in sale_order_id:
                if not order.x_is_contract_quote:
                    raise ValidationError(
                        " This is NOT a Subscription Quote so no Contract will be created")
                if order.state == 'draft':
                    raise ValidationError(
                        "You can't Create a subscription while the Quote is in Draft mode !\n You must first Confirm Sale")
                create_contract = order_line_obj.search([('product_id.categ_id.name', 'in', ['main product', 'component']),('order_id', '=', order.id)])
                if not create_contract:
                    raise ValidationError(
                        " There is no Machine or Component on this Order, so no Contract will be created")
                # First delete all subscriptions already linked to this Sales order ???
                subscription_obj.search([('x_sale_order_id', '=', order.id)]).unlink()
                """Create a new subscription for this machine"""
                sub_header = {
                    'partner_id': order.partner_id.id,
                    'user_id': order.partner_id.user_id.id,
                    'x_sale_order_id': order.id,
                    'template_id': 1
                }

                # This logic only caters for instances where kits have been used.
                # Any products added to the sales order afterwards, must be added manually to a subscription.
                # probably best to skip over any product that is not a kit - Not sure
                grouped_lines = groupby(order.order_line, key=lambda m: m.x_kit_num)
                #logging.warning("group are %s", grouped_lines)
                for group, lines in grouped_lines:
                    category = 'main product'
                    #logging.warning("1. group lines are [%s] %s", group, lines)


                    for i in range(len(lines)):
                        if lines[i].display_type == 'line_section':
                            continue
                        logging.warning("The current line is [%s] [%s]", lines[i].product_id.name,
                                                lines[i].product_id.categ_id.name)
                        if lines[i].product_id.categ_id.name in ['main product', 'component'] :

                            if (lines[i].product_id.categ_id.name == 'main product'):
                                logging.warning("===Creating contract %s %s", lines[i].product_id.name,
                                                lines[i].product_id.categ_id.name)
                                lines = [lines[i]] + lines[:i] + lines[i + 1:]
                                new_subscription_id = subscription_obj.create(sub_header)
                                logging.warning("The new_subscription_id is %s", new_subscription_id)

                    for i in range(len(lines)):
                        logging.warning("Working with line %s", lines[i].name)
                        if lines[i].product_id.categ_id.name in ['main product']:

                            move_line = stock_move_obj.search([('origin','=',lines[i].order_id.name),('sale_line_id', '=', lines[i].id),('state','!=','cancel')]).id
                            serial = stock_move_line_obj.search([('move_id', '=', move_line)],limit=1).lot_id

                            lines[i].subscription_id = new_subscription_id.id
                            if not serial:
                                delivery_note = self.env['stock.picking'].search([('sale_id', '=', order.id)]).name
                                # msg = "Sale Line item: \n Product Category: \n You can't Create a subscription until Serial Numbers have been allocated by Stores !\n"
                                # msg = msg + "Please ask Stores to allocate Serial Numbers to this machine",line.product_id,
                                # raise ValidationError(msg)
                                raise UserError(_("UNABLE TO CREATE CONTRACT\n\n"
                                                  "Sale Line item: %s \n"
                                                  "Category: %s \n"
                                                  "Tracking: %s \n"
                                                  "Exception: 1. Item requires a serial number if either a main product or component.\n"
                                                  "\t           2. Check if the item is tracked by serial number.\n"
                                                  "\t           3. Check if the Product Category is correct.\n"
                                                  "\t           4. Check if a delivery was completed for this Sales order.\n"
                                                  "\t           5. Check if a serial number has been assigned if tracking by serial number is set for this product.") %
                                                (lines[i].product_id.name, lines[i].product_id.categ_id.name,
                                                 lines[i].product_id.tracking))


                            analytic_exist = analytic_obj.search([('name','=', serial.name)])
                            if analytic_exist:
                                # Update the partner on the existing record
                                analytic_exist.write({
                                    'partner_id': order.partner_id.id,
                                })
                            else:
                                # Now create an Analytic Account based on the Serial Number of the Main Product
                                res = {'name': serial.name,
                                       'group_id': 3,
                                       'partner_id': order.partner_id.id,
                                       }
                                analytic_obj.create(res)
                            lot = stock_production_lot_obj.search([('id', '=', serial.id), ])
                            lot.x_subscription_id = new_subscription_id.id
                            dlv_address = order.partner_id.address_get(['delivery'])
                            lot.x_dlv_id = self.env['res.partner'].search([('id', '=', dlv_address['delivery'])])
                            lot.x_main_product = 1
                            lot.x_increase_rental_percent = order.x_finance_escalation
                            lot.x_increase_rental_date = datetime.today() + relativedelta(months=12)
                            # Now create Subscription lines from preloaded charges on this product
                            for rec in lines[i].product_id.x_machine_charge_ids:
                                lines[i].subscription_id = new_subscription_id.id
                                show = False
                                if rec.product_id.categ_id.name == 'copies':
                                    show = True
                                    res = {
                                        'name': rec.name,
                                        'uom_id': 1,
                                        'product_id': rec.product_id.id,
                                        'quantity': 0,
                                        'price_unit': rec.copies_price_1,
                                        'analytic_account_id': new_subscription_id.id,
                                        'x_copies_show': show,
                                        'x_product_id': lines[i].product_id,
                                        'x_serial_number_id': serial.id,
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
                                        'analytic_account_id': new_subscription_id.id,
                                        'x_copies_show': show,
                                        'x_product_id': lines[i].product_id,
                                        'x_serial_number_id': serial.id,
                                    }
                                    line_id = subscription_line_obj.create(res)

                            if order.x_finance_rental:
                                prod_id = self.env['product.product'].search([('name', '=', 'Finance Deal')])
                                if not prod_id:
                                    raise ValidationError(
                                        "You need to create a Product of type Consumable called 'Finance Deal'")
                                mth = int(order.x_finance_months)
                                end_date = datetime.today() + relativedelta(months=mth)
                                res = {
                                    'name': 'Monthly Rental',
                                    'analytic_account_id': new_subscription_id.id,
                                    # This is the key back to the Subscription and has nothing to do with analytic accounts
                                    'uom_id': 1,
                                    'product_id': prod_id.id,
                                    'x_copies_show': False,
                                    'quantity': 1,
                                    'price_unit': lines[i].x_rental_amount,
                                    'x_serial_number_id': serial.id,
                                    'x_end_date1': end_date,
                                    'x_start_date1_billable': False,  # Bank will do the billing
                                }
                            logging.warning("Res is %s", res)
                            subscription_line_obj.create(res)

                        # Set the correct delivery address for the companent if tracked by serial number
                        # Add the serial number to the description if tracked by serial number
                        if lines[i].product_id.categ_id.name in ['component']:
                            _logger.warning("===COMPONENTS - The line we are working with is %s",lines[i].name )
                            #
                            lines[i].subscription_id = new_subscription_id.id
                            # If the component is a serialized item, set the delivery address on the lot
                            if lines[i].product_id.tracking:
                                _logger.warning("===2. The line we are working with is %s", lines[i].name)
                                move_line = stock_move_obj.search([('sale_line_id', '=', lines[i].id),('state','!=','cancel')]).id
                                serial = stock_move_line_obj.search([('move_id', '=', move_line)],limit=1).lot_id
                                lot = stock_production_lot_obj.search([('id', '=', serial.id)])
                                lot.x_dlv_id = lines[i].delivery_addr_id

                                # Set the serial number of the component onto the description
                                name = lines[i].name

                            else:
                                name = lines[i].name
                            res = {
                                'product_id': lines[i].product_id.id,
                                'uom_id' : lines[i].product_uom.id,
                                'quantity': lines[i].product_uom_qty,
                                'name': name,
                                'price_unit': lines[i].price_unit,
                                'analytic_account_id': new_subscription_id.id,
                                'x_start_date1_billable': False,
                                'x_billing_frequency': 0,


                            }
                            subscription_line_obj.create(res)
                        # End the end of the program set all the serialized items on the Equipment on the contract
                        move_line = stock_move_obj.search(
                            [('sale_line_id', '=', lines[i].id), ('state', '!=', 'cancel')]).id
                        serials = stock_move_line_obj.search([('move_id', '=', move_line)]).lot_id
                        for serial in serials:
                            new_subscription_id.x_machine_ids = [(4, serial.id, 0)]

    @api.depends('partner_id', 'date_order')
    def _compute_analytic_account_id(self):
        for order in self:
            if order.x_lot_id:
                _logger.warning("===========1. Setting the analytic account")
                analytic = self.env['account.analytic.account'].search([('name','=',order.x_lot_id.name)]).id
                order.analytic_account_id = analytic
                _logger.warning("===========1. Setting the analytic account %s",order.analytic_account_id )

            if not order.analytic_account_id:

                default_analytic_account = order.env['account.analytic.default'].sudo().account_get(
                    partner_id=order.partner_id.id,
                    user_id=order.env.uid,
                    date=order.date_order,
                    company_id=order.company_id.id,
                )
                order.analytic_account_id = default_analytic_account.analytic_id
                _logger.warning("===========2. Setting the analytic account %s",order.analytic_account_id)

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        _logger.warning("************** Line 536")
        self.ensure_one()
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(
                _('Please define an accounting sales journal for the company %s (%s).', self.company_id.name,
                  self.company_id.id))

        invoice_vals = {
            'ref': self.client_order_ref or '',
            'move_type': 'out_invoice',
            'narration': self.note,
            'currency_id': self.pricelist_id.currency_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'user_id': self.user_id.id,
            'invoice_user_id': self.user_id.id,
            'team_id': self.team_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(
                self.partner_invoice_id.id)).id,
            'partner_bank_id': self.company_id.partner_id.bank_ids.filtered(
                lambda bank: bank.company_id.id in (self.company_id.id, False))[:1].id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'payment_reference': self.partner_id.x_account_number,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
            'x_main_partner': self.partner_id.id,
        }
        return invoice_vals
    def _get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for line in self.order_line:
            logging.warning("product is %s %s %s", line.name, line.qty_to_invoice, line.product_id.x_invoice_ok)
            if line.product_id.x_invoice_ok == True:
                continue
            if line.display_type == 'line_section':
                # Only invoice the section if one of its lines is invoiceable
                pending_section = line
                continue
            if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision) and line.product_id.x_invoice_ok == True:
                logging.warning("Tracking you")
                continue
            if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                if line.is_downpayment:
                    # Keep down payment lines separately, to put them together
                    # at the end of the invoice, in a specific dedicated section.
                    down_payment_line_ids.append(line.id)
                    continue
                if pending_section:
                    invoiceable_line_ids.append(pending_section.id)
                    pending_section = None
                invoiceable_line_ids.append(line.id)

        return self.env['sale.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_rental_amount = fields.Float(string="Rental Amount")
    x_bom_parent = fields.Boolean(string="Bom Parent")
    x_kit_num = fields.Float(string="Kit Line Number")

    @api.onchange('product_id')
    def onchange_product_id(self, context=None):
        if not self.product_id:
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

    """This doesnt seem to be called from anywhere """

    def add_component(self):
        list = []
        for id in self.product_id.x_optional_component_ids:
            list.append(id.id)
        return {
            'name': self.name,
            'view_type': 'form',
            'view_mode': 'many2many',
            'res_model': 'product.template',  # this is the which form i want when i clcik button
            'views': [(1685, 'tree')],
            'type': 'ir.actions.act_window',
            'target': 'current:',
            'domain': [('id', '=', list)],
            'context': self.env.context,
        }
        rec = super(SaleOrderLine, self).create(vals_list)
        return rec

    def _timesheet_create_task_prepare_values(self, project):
        self.ensure_one()
        planned_hours = self._convert_qty_company_hours(self.company_id)
        sale_line_name_parts = self.name.split('\n')
        title = sale_line_name_parts[0] or self.product_id.name
        description = '<br/>'.join(sale_line_name_parts[1:])
        _logger.warning("testing if this code is run without a product")
        return {
            'name': title if project.sale_line_id else '%s: %s' % (self.order_id.name or '', title),
            'planned_hours': planned_hours,
            'partner_id': self.order_id.partner_id.id,
            'email_from': self.order_id.partner_id.email,
            'description': description,
            'project_id': project.id,
            'sale_line_id': self.id,
            'sale_order_id': self.order_id.id,
            'company_id': project.company_id.id,
            'user_ids': False,  # force non assigned task, as created as sudo()
            'x_serial_number_id': self.order_id.x_lot_id.id or False,

        }
