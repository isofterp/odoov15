#!/usr/bin/env python
from odoo import api, fields, models, _
import logging
from dateutil.relativedelta import relativedelta
from datetime import datetime
from dateutil.parser import parse

_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    # this is commented out to run the conversion program
    #  !!!!!!!!!! Uncomment the below to go live !!!!!
    #   25/10/2022 I dont beleieve we need this anymore. The create is in the sale.py

    #   Must be active once conversion has been run
    #@api.model
    # def create(self, vals):
    #     print('@21 create sale_subscription.py',vals)
    #     list_of_ids = []
    #
    #     # Now create the Subscription - THIS routine is to be used when automatic creation of Subscription fro Sales Order
    #     new_rec = super(SaleSubscription, self).create(vals)
    #
    #     subscription_line_obj = self.env['sale.subscription.line']
    #     production_lot_obj = self.env['stock.production.lot']
    #     machines = vals.get('x_machine_ids')
    #     print('list of mac', machines)
    #     if machines:
    #         list_of_ids = machines[0][2]
    #     if list_of_ids:
    #         print('list of  ids', list_of_ids)
    #         for x in list_of_ids:
    #             rec_found = subscription_line_obj.search_count([('line.x_serial_number_id', '=', x)])
    #             if rec_found:
    #                 continue
    #             else:
    #                 print("need to create charges for ", x)
    #                 mac = production_lot_obj.search([('id', '=', x)])
    #                 mac.x_in_use = True
    #                 for rec in mac.product_id.x_machine_charge_ids:
    #                     show = False
    #                     if rec.product_id.categ_id.name == 'copies':
    #                         show = True
    #                         res = {
    #                             'name': " Tier One",
    #                             'uom_id': 1,
    #                             'product_id': rec.product_id.id,
    #                             'quantity': 0,
    #                             'price_unit': rec.copies_price_1,
    #                             'analytic_account_id': new_rec.id,
    #                             'x_copies_show': show,
    #                             'x_product_id': mac.product_id,
    #                             'line.x_serial_number_id': mac.id,
    #                             'x_copies_minimum': rec.minimum_charge,
    #                             'x_copies_free': rec.copies_free,
    #                             'x_copies_vol_1': rec.copies_vol_1,
    #                             'x_copies_price_1': rec.copies_price_1,
    #                             'x_copies_vol_2': rec.copies_vol_2,
    #                             'x_copies_price_2': rec.copies_price_2,
    #                             'x_copies_vol_3': rec.copies_vol_2,
    #                             'x_copies_price_3': rec.copies_price_3,
    #                         }
    #                         line_id = subscription_line_obj.create(res)
    #
    #                     else:
    #                         res = {
    #                             'name': rec.name,
    #                             'uom_id': 1,
    #                             'product_id': rec.product_id.id,
    #                             'quantity': rec.qty,
    #                             'price_unit': rec.price,
    #                             'analytic_account_id': new_rec.id,
    #                             'x_copies_show': show,
    #                             'x_product_id': mac.product_id,
    #                             'line.x_serial_number_id': mac.id,
    #
    #                         }
    #                         line_id = subscription_line_obj.create(res)
    #
    #     return new_rec

    #   need attention - wont work if called from sales order
    # def write(self, vals):
    #     #print('in write')
    #     list_of_origin_ids = self._origin.x_machine_ids
    #     subscription_line_obj = self.env['sale.subscription.line']
    #     production_lot_obj = self.env['stock.production.lot']
    #     if 'x_machine_ids' in vals.keys():
    #         machines = vals.get('x_machine_ids')
    #         print ('machines', machines,len(machines))  # this returns [[6, False, [2, 3, 6]]]
    #         list_of_ids = machines[0][2]  # this extracts [2, 3, 6] from [[6, False, [2, 3, 6]]]
    #         for i in list_of_origin_ids:
    #             if i.id not in machines[0][2]:
    #                 # print('Not found  so deleted', i.id)
    #                 production_lot_obj.search([('id', '=', i.id)]).write({'x_in_use': False})
    #
    #         for x in list_of_ids:
    #             mac = production_lot_obj.search([('id', '=', x)])
    #             mac.x_in_use = True
    #             mac.ref = self.display_name
    #             print ('xxxxxxxxx=',x)
    #             rec_found = subscription_line_obj.search_count(
    #                 [('analytic_account_id', '=', self.id), ('x_serial_number_id', '=', x)])
    #             if rec_found:
    #                 continue
    #             else:
    #                 # print("need to create charges for ", x,self.id)
    #                 for rec in mac.product_id.x_machine_charge_ids:
    #                     show = False
    #                     if rec.product_id.categ_id.name == 'copies':
    #                         show = True
    #                         res = {
    #                             'analytic_account_id': self.id,
    #                             'name': " Tier One",
    #                             'uom_id': 1,
    #                             'product_id': rec.product_id.id,
    #                             'quantity': 0,
    #                             'price_unit': rec.copies_price_1,
    #                             'x_copies_show': show,
    #                             'x_product_id': mac.product_id,
    #                             'line.x_serial_number_id': mac.id,
    #                             'x_copies_minimum': rec.minimum_charge,
    #                             'x_copies_free': rec.copies_free,
    #                             'x_copies_vol_1': rec.copies_vol_1,
    #                             'x_copies_price_1': rec.copies_price_1,
    #                             'x_copies_vol_2': rec.copies_vol_2,
    #                             'x_copies_price_2': rec.copies_price_2,
    #                             'x_copies_vol_3': rec.copies_vol_2,
    #                             'x_copies_price_3': rec.copies_price_3,
    #                         }
    #                         line_id = subscription_line_obj.create(res)
    #
    #                     else:
    #                         res = {
    #                             'analytic_account_id': self.id,
    #                             'name': rec.name,
    #                             'uom_id': 1,
    #                             'product_id': rec.product_id.id,
    #                             'quantity': rec.qty,
    #                             'price_unit': rec.price,
    #                             'x_copies_show': show,
    #                             'x_product_id': mac.product_id,
    #                             'line.x_serial_number_id': mac.id,
    #                         }
    #                         line_id = subscription_line_obj.create(res)
    #     return super(SaleSubscription, self).write(vals)

    """ This _name_search is NOT firing """
    @api.model
    def name_search(self, name='', args=None, operator='ilike',limit=100, name_get_uid=None):
        print("*** in my name_search")
        args = [] if args is None else args.copy()
        print('@179 in my sale_subscription ,args', args)
        if not (name == '' and operator == 'ilike'):
            args += ['|', '|',
                     ('x_serial_number_id', operator, name),
                     ('analytic_account_id', operator, name),
                     ('analytic_account_id.partner_id.x_account_number', operator, name)
                     ]
        return super(SaleSubscription, self)._name_search(name='', args=args, operator='ilike', limit=limit,
                                                          name_get_uid=name_get_uid)

    x_add_hoc_increase = fields.Selection(selection=[('yes', 'Yes'), ('no', 'No')], default='yes',
                                          string='Add Hoc Increases')
    x_third_party_rental_billing = fields.Selection(selection=[('yes', 'Yes'), ('no', 'No')], default='no',
                                                    string='3rd Party Rental Billing')
    x_account_number = fields.Char('Account Number', related='partner_id.x_account_number', index=True)
    x_sale_order_id = fields.Many2one('sale.order', 'Sales Order')
    x_rental_group_id = fields.Many2one('subscription.rental.group', 'Rental Group')

    x_ceded_reference = fields.Char('Ceded Ref Number')
    x_bank_name = fields.Char('Bank Name')
    x_machine_ids = fields.Many2many('stock.production.lot', 'sale_subscription_subscription_stock_production_lot_rel',
                                     'sale_subscription_id', 'stock_production_lot_id', string='Machine',
                                     ondelete='cascade')

    def open_sale_orders(self):
        context = self._context.copy()
        sale_ids = self.env['sale.order'].search(
            [('partner_id', '=', self.partner_id.id), ('invoice_status', '=', 'to invoice')])
        # print('sale_ids',sale_ids)
        name = _('Sales Order Lines to Invoice of %s') % (self.code)
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'context': context,
            # 'domain': [('order_id', 'in', sale_ids)],
            'domain': [('partner_id', '=', self.partner_id.id), ('invoice_status', '=', 'to invoice')],
            'res_model': 'sale.order',
            'nodestroy': True,
        }

    def create_sales_order(self):
        view_id = self.env.ref('sale.view_order_form').id
        context = self._context.copy()
        print('self id', self.id)
        for lot in self.x_machine_ids:
            if lot.x_main_product:
                dlv_ids = lot.x_dlv_id.id
                lot_ids = lot.id
                print('Delivery adsd', dlv_ids)

        context.update({'default_partner_id': self.partner_id.id,
                        'default_analytic_account_id': self.analytic_account_id.id,
                        'default_x_sale_subscription_id': self.id,
                        'default_dlv_ids': dlv_ids,
                        'default_x_lot_id': lot_ids,
                        })

        return {
            'name': 'Sale Order',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(view_id, 'form')],
            'res_model': 'sale.order',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'res_id': False,
            'target': 'new',
            'context': context,
        }

    def _prepare_invoice_lines(self, fiscal_position):
        print("@229 My _prepare_invoice_lines in sale_subscription.py")
        self.ensure_one()
        revenue_date_start = self.recurring_next_date
        periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
        revenue_date_stop = revenue_date_start + relativedelta(
            **{periods[self.recurring_rule_type]: self.recurring_interval}) - relativedelta(days=1)
        return self._isoft_prepare_invoice_line(fiscal_position, revenue_date_start, revenue_date_stop)

    def _isoft_prepare_invoice_line(self, fiscal_position, date_start=False, date_stop=False):
        print('fisacl=', fiscal_position)
        lines = []
        increment_copies = increment_rental = increment_service = mac_serial = ''
        analytic_obj = self.env['account.analytic.account']
        for line in self.recurring_invoice_line_ids:
            mac_serial = "[" + line.x_serial_number_id.product_id.default_code + "]" + line.x_serial_number_id.name + " "
            machine = self.env['stock.production.lot'].search([('id', '=', line.x_serial_number_id.id)])
            account = analytic_obj.search([('name', '=', line.x_serial_number_id.name)])

            if machine:
                # print("@262", line.name, line.product_id.categ_id.name)
                # print('machine',machine.x_increase_copies_date)
                if machine.x_increase_rental_date:
                    if self.recurring_next_date >= machine.x_increase_rental_date:
                        if line.product_id.categ_id.name == 'rental':
                            line.price_unit += machine.x_increase_rental_percent * line.price_unit / 100
                            increment_rental = 'yes'
                            # print ('rental increase',line.price_unit, machine.x_increase_rental_date)
                if machine.x_increase_service_date:
                    if self.recurring_next_date >= machine.x_increase_service_date:
                        if line.product_id.categ_id.name == 'service':
                            line.price_unit += machine.x_increase_service_percent * line.price_unit / 100
                            increment_service = 'yes'
                            print('service increase', line.price_unit, machine.x_increase_service_date)
                if machine.x_increase_copies_date:
                    if self.recurring_next_date >= machine.x_increase_copies_date:
                        print(self.recurring_next_date, machine.x_increase_copies_date)
                        if line.product_id.categ_id.name == 'copies':
                            line.x_copies_price_1 += machine.x_increase_copies_percent * line.x_copies_price_1 / 100
                            line.x_copies_price_2 += machine.x_increase_copies_percent * line.x_copies_price_2 / 100
                            line.x_copies_price_3 += machine.x_increase_copies_percent * line.x_copies_price_3 / 100
                            increment_copies = 'yes'
            if line.x_end_date1:
                if self.recurring_next_date >= line.x_end_date1 and not x_third_party_rental_billing:
                    # If the end_date1 has been reached, that means the bank will stop billing so we set the billing
                    # indicator to 'yes' and this program will start creating invoices instead of the Bank (3rd party).
                    # However, if the x_third_party_rental_billing field is set to 'yes' then that means the
                    # Bank (3rd party) will continue billing and the billing indicator will remain off.
                    line.x_start_date1_billable = True
                    group_id = self.env['subscription.rental.group'].search(
                        [('group_type', '=', 'C'), ('group_code', '=', 10)])  # should point to Secondary Rental
                    if group_id:
                        self.x_rental_group_id = group_id[0]
            # print (line.name)
            # print (line.x_start_date1 ,line.x_start_date1_billable )
            if line.x_start_date1:
                if line.x_start_date1 > self.recurring_next_date or not line.x_start_date1_billable:
                    # print('product = %s next recurring invoice date = %s start date = %s billable=%s' % (
                    # line.name, self.recurring_next_date, line.x_start_date1, line.x_start_date1_billable))
                    continue
            if line.x_billing_frequency > 1:
                # print("billing freq", line.x_billing_frequency, line.x_billing_hold)
                if line.x_billing_frequency - line.x_billing_hold == 1:
                    # print('here 1')
                    line.x_billing_hold = 0
                else:
                    line.x_billing_hold += 1
                    # print('here 2', line.x_billing_hold)
                    continue

            ###    LOGIC TO CREATE TIERS - NOT SURE WHERE TO PUT THIS BECAUSE N CONVERSION AND NORMAL PROCESING
            if line.product_id.categ_id.name == 'copies':
                copies_total_value = 0
                qty_tier_1 = 0
                qty_tier_2 = 0
                qty_tier_3 = 0
                if line.quantity > line.x_copies_vol_1:
                    qty_tier_1 = line.x_copies_vol_1
                    copies_total_value = line.x_copies_vol_1 * line.x_copies_price_1
                    hold_read = line.quantity - line.x_copies_vol_1
                    # print ('@88,line',line.x_copies_vol_1,hold_read,qty_tier_1)
                    # print(line.x_copies_vol_2, hold_read)
                    if hold_read > line.x_copies_vol_2:
                        qty_tier_2 = line.x_copies_vol_2
                        copies_total_value += line.x_copies_vol_2 * line.x_copies_price_2
                        hold_read -= line.x_copies_vol_2
                        # print ('@94,line', line.x_copies_vol_2, hold_read, qty_tier_2)
                        qty_tier_3 = hold_read
                        copies_total_value += hold_read * line.x_copies_price_3
                    else:
                        qty_tier_2 = hold_read
                        copies_total_value += hold_read * line.x_copies_price_2
                        # print ('@99,line', qty_tier_2,hold_read)
                else:
                    if line.quantity > 0:
                        qty_tier_1 = line.quantity
                        copies_total_value = qty_tier_1 * line.x_copies_price_1

                # Create Tiers or Minimum Billing
                if copies_total_value < line.x_copies_minimum:
                    line_vals = {
                        'subscription_id': line.analytic_account_id.id,
                        'ref': "Contract Number " + line.analytic_account_id.name,
                        'quantity': 1,
                        # vals.update({'specific_price': line.x_copies_price_1}),
                        'price_unit': line.x_copies_minimum,
                        'product_uom_id': line.uom_id.id,
                        'product_id': line.product_id.id,
                        'tax_ids': [(6, 0, line.product_id.taxes_id.filtered(
                            lambda t: t.company_id == line.analytic_account_id.company_id).ids)],
                        'name': mac_serial + str(
                            copies_total_value) + " value below Minimum - Min Billing Applies @ Value",
                        # 'analytic_account_id': analyticAccount_id,
                        # 'analytic_tag_ids':  [(4,line.x_serial_number_id.id)],
                    }
                    lines.append(line_vals)

                else:
                    if qty_tier_1 > 0:
                        line_vals = {
                            'subscription_id': line.analytic_account_id.id,
                            'ref': "Contract Number " + line.analytic_account_id.name,
                            'quantity': qty_tier_1,
                            'product_uom_id': line.uom_id.id,
                            'product_id': line.product_id.id,
                            'tax_ids': [(6, 0, line.product_id.taxes_id.filtered(
                                lambda t: t.company_id == line.analytic_account_id.company_id).ids)],
                            'price_unit': line.x_copies_price_1,
                            'name': mac_serial + line.name + " Tier One",
                            # 'analytic_account_id':analyticAccount_id
                            # 'analytic_tag_ids':  [(4,line.x_serial_number_id.id)],
                            # 'subscription_start_date': date_start,
                            # 'subscription_end_date': date_stop,
                        }
                        # print ('tier 1=', line_vals)

                        lines.append(line_vals)
                    if qty_tier_2 > 0:
                        line_vals = {
                            'subscription_id': line.analytic_account_id.id,
                            'ref': "Contract Number " + line.analytic_account_id.name,
                            'quantity': qty_tier_2,
                            # vals.update({'specific_price': line.x_copies_price_1}),
                            'product_uom_id': line.uom_id.id,
                            'product_id': line.product_id.id,
                            'tax_ids': [(6, 0, line.product_id.taxes_id.filtered(
                                lambda t: t.company_id == line.analytic_account_id.company_id).ids)],

                            'price_unit': line.x_copies_price_2,
                            'name': mac_serial + line.name + " Tier Two",
                            # 'analytic_account_id': analyticAccount_id,
                            # 'analytic_tag_ids':  [(4,line.x_serial_number_id.id)],

                        }
                        lines.append(line_vals)
                    if qty_tier_3 > 0:
                        line_vals = {
                            'subscription_id': line.analytic_account_id.id,
                            'ref': "Contract Number " + line.analytic_account_id.name,
                            'quantity': qty_tier_3,
                            # vals.update({'specific_price': line.x_copies_price_1}),
                            'product_uom_id': line.uom_id.id,
                            'product_id': line.product_id.id,
                            'tax_ids': [(6, 0, line.product_id.taxes_id.filtered(
                                lambda t: t.company_id == line.analytic_account_id.company_id).ids)],

                            'price_unit': line.x_copies_price_3,
                            'name': mac_serial + line.name + " Tier Three",
                            # 'analytic_account_id': analyticAccount_id,
                            # 'analytic_tag_ids':  [(4,line.x_serial_number_id.id)],
                        }

                        lines.append(line_vals)

                    line.x_copies_previous = line.x_copies_last
                    line.x_email_count = 0
                    line.quantity = 0
            else:
                # print('Non copies')
                print(line.x_serial_number_id.id, line.x_serial_number_id.name)
                line_vals = {
                    'subscription_id': line.analytic_account_id.id,
                    'ref': "Contract Number " + line.analytic_account_id.name,
                    'product_uom_id': line.uom_id.id,
                    'product_id': line.product_id.id,
                    'tax_ids': [(6, 0, line.product_id.taxes_id.filtered(
                        lambda t: t.company_id == line.analytic_account_id.company_id).ids)],
                    'quantity': line.quantity,
                    # vals.update({'specific_price': line.x_copies_price_1}),
                    'price_unit': line.price_unit,
                    'name': mac_serial + line.name,
                    # 'analytic_account_id': analyticAccount_id,
                    # 'analytic_tag_ids':  [(4,line.product_id.categ_id.id)],
                }
                #('ana tag=', line.product_id.categ_id.id, line.product_id.categ_id)
                # print('@439',line_vals)

                lines.append(line_vals)

        print("===================returning the following", lines)
        if increment_copies == 'yes':
            increment_copies = ''
            if machine.x_increase_copies_date:
                machine.x_increase_copies_date = machine.x_increase_copies_date + relativedelta(years=+1)

        if increment_service == 'yes':
            increment_service = ''
            if machine.x_increase_service_date:
                machine.x_increase_service_date = machine.x_increase_service_date + relativedelta(years=+1)

        if increment_rental == 'yes':
            increment_rental == ''
            if machine.x_increase_rental_date:
                machine.x_increase_rental_date = machine.x_increase_rental_date + relativedelta(years=+1)

        return lines

    def _recurring_create_invoice(self, automatic=False):
        rec = super(SaleSubscription, self)._recurring_create_invoice(automatic=automatic)
        rec.write({'ref': self.name})
        return rec

    def _find_mail_template(self, force_confirmation_template=False):
        template_id = False
        template_id = int(
            self.env['mail.template'].search([('name', '=', 'Contracts: Machine Meterreading')]))
        return template_id

    # def action_meterreading_send(self):
    #     self.ensure_one()
    #     template_id = self._find_mail_template()
    #     logging.warning("template is %s", template_id)
    #     lang = self.env.context.get('lang')
    #     template = self.env['mail.template'].browse(template_id)
    #     if template.lang:
    #         lang = template._render_template(template.lang, 'sale.subscription', self.ids[0])
    #     ctx = {
    #         'default_model': 'sale.subscription',
    #         'default_res_id': self.id,
    #         'default_use_template': bool(template_id),
    #         'default_template_id': template_id,
    #         'default_composition_mode': 'comment',
    #         'dbname': self._cr.dbname,
    #         'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url',
    #                                                                      default='http://localhost:8069'),
    #         # 'custom_layout': "mail.mail_notification_paynow",
    #         'force_email': True,
    #         # 'model_description': self.with_context(lang=lang).type_name,
    #     }
    #     # logging.warning("Context is %s", ctx)
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'mail.compose.message',
    #         'views': [(False, 'form')],
    #         'view_id': False,
    #         'target': 'new',
    #         'context': ctx,
    #     }

    def cron_meter_reading_bulk_mail(self, context=None):
        message_0 = "Could you please fill in the latest meter reading figures for the following:"
        message_1 = "This is your second reminder to enter your meter readings"
        message_2 = "This is your FINAL reminder to enter your meter readings"

        line_ids = self.env['sale.subscription.line'].search(['|', ('name', '=', 'Black copies'),
                                                              ('name', '=', 'Colour copies'),
                                                              ('quantity', '=', 0)])
        email_subject = 'Meter Reading Inputs Required for ' + self.env.user.company_id.name
        mail = self.env['mail.mail']
        res_user_obj = self.env['res.users']
        user_id = res_user_obj.browse(self.env.context.get('uid'))
        email_from = user_id.partner_id.email
        email_to = ''
        previous_serial_number = ''
        for line in line_ids:
            serial_number = line.x_serial_number_id.name
            if serial_number == previous_serial_number: continue
            previous_serial_number = serial_number
            product = line.x_serial_number_id.product_id.name
            email_person = ''
            if line.x_serial_number_id.x_dlv_id.email:  # If the machine has an email  address use it
                email_to = line.x_serial_number_id.x_dlv_id.email
                email_person = line.x_serial_number_id.x_dlv_id.name
            else:  # send am email to the Company warning of no email address
                print("no email")
                email_body = "<div>This Contract: " + line.analytic_account_id.code + " has no email address. </br>Please phone " + line.analytic_account_id.partner_id.name
                email_body += " on " + line.analytic_account_id.partner_id.phone + " and enter the last meter readings for "
                email_body += "</br>" + product + " Serial Number: " + serial_number + "</div>"
                email_body += "<div style = 'text-align: center; margin: 16px 0px 16px 0px;' >"
                email_body += "<a href = copytype-billing.isofterp.co.za/my/contracts/?id=" + line.analytic_account_id.code + " </a>Click to capture readings"
                email_body += "</div>"
                mail_values = {
                    'email_from': email_from,
                    'email_to': email_from,
                    'subject': "WARNING from the  Meter Reading Email System",
                    'body_html': email_body,
                    'state': 'outgoing',
                    'scheduled_date': datetime.now(),
                }
                # print("Mail values are %s", mail_values)
                if line.analytic_account_id.code == '11104580':
                    # if line.analytic_account_id.partner_id.id == 186:  # KaapAgrie
                    self.message_post(body=email_body)
                    mail_out = mail.create(mail_values)
                    # mail.send(mail_out)
                    continue
            if line.x_email_count == 0:
                message = message_0
            else:
                if line.x_email_count == 1:
                    message = message_1
                else:
                    message = message_2

            email_body = "<div>Good day&nbsp; " + email_person + ',<div><br></div><div>' + message + '<br/>' + 'Machine: ' + product \
                         + "<br/> Serial Number: " + serial_number + " <br/>Contract Number: " + line.analytic_account_id.code + "</div>"
            # !!!!!!!!! take the follwing line out after teting !!!!!!!!!!!!!!!!!!!!!!!!!!
            email_body += "<div> FOR TESTING - the real email address for " + email_person + " is " + email_to
            email_body += "<div style = 'text-align: center; margin: 16px 0px 16px 0px;' >"
            email_body += "<a href = copytype-billing.isofterp.co.za/my/contracts/?id=" + line.analytic_account_id.code + " </a>Click to capture readings"
            email_body += "</div>"

            email_to = 'sue@copytype.co.za'  ################   !!!!!!!!!!!   Testing email address - remove to go live  !!!!!
            email_to = 'roly@isoft.co.za'
            mail_values = {
                'email_from': email_from,
                'email_to': email_to,
                'subject': email_subject,
                'body_html': email_body,
                'state': 'outgoing',
                'scheduled_date': datetime.now(),
            }
            # print(mail_values)

            # if line.analytic_account_id.partner_id.id == 186:  # KaapAgrie
            # print("we are here at last", line.analytic_account_id.partner_id.id)
            if line.analytic_account_id.code == '11104580':
                self.message_post(
                    body=" THIS needs to change for go live " + email_body + " THIS needs to change for go live ")
                mail_out = mail.create(mail_values)
                # mail.send(mail_out)
                line.x_email_count += 1
