# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo.tools.float_utils import float_round as round
from odoo import api, fields, models, _
from datetime import datetime, time, date
from dateutil.relativedelta import relativedelta
from lxml import etree
import base64
import re
from odoo import tools
# import odoo.report
import calendar
import logging


class account_move(models.Model):
    _inherit = 'account.move'
    _order = 'invoice_date_due'

    def _get_result(self):
        for aml in self:
            aml.result = 0.0
            aml.result = aml.amount_total_signed - aml.credit_amount

    def _get_credit(self):
        for aml in self:
            aml.credit_amount = 0.0
            aml.credit_amount = aml.amount_total_signed - aml.amount_residual_signed

    credit_amount = fields.Float(compute='_get_credit', string="Credit/paid")
    result = fields.Float(compute='_get_result', string="Balance")  # 'balance' field is not the same


class Res_Partner(models.Model):
    _inherit = 'res.partner'

    # attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    def _get_amounts_and_date_amount(self):
        user_id = self._uid
        company = self.env['res.users'].browse(user_id).company_id

        current_date = datetime.now().date()

        for partner in self:
            partner.do_process_monthly_statement_filter()
            amount_due = amount_overdue = 0.0
            supplier_amount_due = supplier_amount_overdue = 0.0
            for aml in partner.balance_invoice_ids:
                if (aml.company_id == company):
                    date_maturity = aml.invoice_date_due or aml.date
                    amount_due += aml.result

                    if (date_maturity <= current_date):
                        amount_overdue += aml.result
            partner.payment_amount_due_amt = amount_due
            partner.payment_amount_overdue_amt = amount_overdue
            for aml in partner.supplier_invoice_ids:
                if (aml.company_id == company):
                    date_maturity = aml.invoice_date_due or aml.date
                    supplier_amount_due += aml.result
                    if (date_maturity <= current_date):
                        supplier_amount_overdue += aml.result
            partner.payment_amount_due_amt_supplier = supplier_amount_due
            partner.payment_amount_overdue_amt_supplier = supplier_amount_overdue

            monthly_amount_due_amt = monthly_amount_overdue_amt = 0.0
            for aml in partner.monthly_statement_line_ids:
                date_maturity = aml.invoice_date_due
                monthly_amount_due_amt += aml.result
                if date_maturity and (date_maturity <= current_date):
                    monthly_amount_overdue_amt += aml.result
            partner.monthly_payment_amount_due_amt = monthly_amount_due_amt

            partner.monthly_payment_amount_overdue_amt = monthly_amount_overdue_amt

    start_date = fields.Date('Start Date', compute='get_dates')
    month_name = fields.Char('Month', compute='get_dates')
    end_date = fields.Date('End Date', compute='get_dates')

    customer_start = fields.Date('Start Date')
    customer_end = fields.Date('End Date')
    customer_bal = fields.Float(string="Customer Bal")

    vendor_start = fields.Date('Start Date')
    vendor_end = fields.Date('End Date')
    vendor_bal = fields.Float(string="Customer Bal")

    vendor_payment_line_ids = fields.One2many('payments.statement.invoice', 'vendor_id', 'Payments Statement Lines')
    customer_payment_line_ids = fields.One2many('payments.statement.invoice', 'partner_id', 'Payments Statement Lines')
    monthly_statement_line_ids = fields.One2many('monthly.statement.line', 'partner_id', 'Monthly Statement Lines')
    supplier_invoice_ids = fields.One2many('account.move', 'partner_id', 'Customer move lines',
                                           domain=[('move_type', 'in', ['in_invoice', 'in_refund']),
                                                   ('state', 'in', ['posted'])])
    balance_invoice_ids = fields.One2many('account.move', 'partner_id', 'Customer move lines',
                                          domain=[('move_type', 'in', ['out_invoice', 'out_refund']),
                                                  ('state', 'in', ['posted'])])

    payment_amount_due_amt = fields.Float(compute='_get_amounts_and_date_amount', string="Balance Due")
    payment_amount_overdue_amt = fields.Float(compute='_get_amounts_and_date_amount',
                                              string="Total Overdue Amount")
    payment_amount_due_amt_supplier = fields.Float(compute='_get_amounts_and_date_amount',
                                                   string="Supplier Balance Due")
    payment_amount_overdue_amt_supplier = fields.Float(compute='_get_amounts_and_date_amount',
                                                       string="Total Supplier Overdue Amount")

    monthly_payment_amount_due_amt = fields.Float(compute='_get_amounts_and_date_amount', string="Balance Due")
    monthly_payment_amount_overdue_amt = fields.Float(compute='_get_amounts_and_date_amount',
                                                      string="Total Overdue Amount")
    current_date = fields.Date(default=fields.date.today())

    first_thirty_day = fields.Float(string="0-30", compute="compute_days")
    thirty_sixty_days = fields.Float(string="30-60", compute="compute_days")
    sixty_ninty_days = fields.Float(string="60-90", compute="compute_days")
    ninty_plus_days = fields.Float(string="90+", compute="compute_days")
    total = fields.Float(string="Total", compute="compute_total")

    def get_dates(self):
        for record in self:
            today = date.today()
            d = today - relativedelta(months=1)

            start_date = date(d.year, d.month, 1)
            end_date = date(today.year, today.month, 1) - relativedelta(days=1)

            record.month_name = calendar.month_name[start_date.month] or False
            record.start_date = str(start_date) or False
            record.end_date = str(end_date) or False

    @api.depends('balance_invoice_ids')
    def compute_days(self):
        today = fields.date.today()
        for partner in self:
            partner.first_thirty_day = 0
            partner.thirty_sixty_days = 0
            partner.sixty_ninty_days = 0
            partner.ninty_plus_days = 0
            if partner.balance_invoice_ids:
                for line in partner.balance_invoice_ids:
                    diff = today - line.invoice_date_due
                    if diff.days <= 30:
                        partner.first_thirty_day = partner.first_thirty_day + line.result
                    elif diff.days > 30 and diff.days <= 60:
                        partner.thirty_sixty_days = partner.thirty_sixty_days + line.result
                    elif diff.days > 60 and diff.days <= 90:
                        partner.sixty_ninty_days = partner.sixty_ninty_days + line.result
                    else:
                        if diff.days > 90:
                            partner.ninty_plus_days = partner.ninty_plus_days + line.result
        return

    @api.depends('ninty_plus_days', 'sixty_ninty_days', 'thirty_sixty_days', 'first_thirty_day')
    def compute_total(self):
        for partner in self:
            partner.total = 0.0
            partner.total = partner.ninty_plus_days + partner.sixty_ninty_days + partner.thirty_sixty_days + partner.first_thirty_day
        return

    def _cron_send_customer_statement(self):
        partners = self.env['res.partner'].search([])
        # partner_search_mode = self.env.context.get('res_partner_search_mode')
        # if partner_search_mode == 'customer':
        if self.env.user.company_id.period == 'monthly':
            partners.do_process_monthly_statement_filter()
            partners.customer_monthly_send_mail()
        else:
            partners.customer_send_mail()
        return True

    def customer_monthly_send_mail(self):
        unknown_mails = 0
        for partner in self:
            partners_to_email = [child for child in partner.child_ids if child.move_type == 'invoice' and child.email]
            if not partners_to_email and partner.email:
                partners_to_email = [partner]
            if partners_to_email:
                for partner_to_email in partners_to_email:
                    mail_template_id = self.env['ir.model.data'].xmlid_to_object(
                        'account_statement.email_template_customer_monthly_statement')
                    if mail_template_id:
                        mail_template_id.send_mail(partner_to_email.id)
                if partner not in partner_to_email:
                    self.message_post([partner.id], body=_('Customer Monthly Statement email sent to %s' % ', '.join(
                        ['%s <%s>' % (partner.name, partner.email) for partner in partners_to_email])))
        return unknown_mails

    def do_process_monthly_statement_filter(self):
        account_invoice_obj = self.env['account.move']
        statement_line_obj = self.env['monthly.statement.line']
        for record in self:

            today = date.today()
            d = today - relativedelta(months=1)

            start_date = date(d.year, d.month, 1)
            end_date = date(today.year, today.month, 1) - relativedelta(days=1)

            from_date = str(start_date)
            to_date = str(end_date)

            domain = [('move_type', 'in', ['out_invoice', 'out_refund']), ('state', 'in', ['posted']),
                      ('partner_id', '=', record.id)]
            if from_date:
                domain.append(('invoice_date', '>=', from_date))
            if to_date:
                domain.append(('invoice_date', '<=', to_date))

            lines_to_be_delete = statement_line_obj.search([('partner_id', '=', record.id)])
            lines_to_be_delete.unlink()

            invoices = account_invoice_obj.search(domain)
            for invoice in invoices.sorted(key=lambda r: r.name):
                vals = {
                    'partner_id': invoice.partner_id.id or False,
                    'state': invoice.state or False,
                    'invoice_date': invoice.invoice_date,
                    'invoice_date_due': invoice.invoice_date_due,
                    'result': invoice.result or 0.0,
                    'name': invoice.name or '',
                    'amount_total': invoice.amount_total or 0.0,
                    'credit_amount': invoice.credit_amount or 0.0,
                    'invoice_id': invoice.id,
                }
                ob = statement_line_obj.create(vals)

    def customer_send_mail(self):
        unknown_mails = 0
        for partner in self:
            #partners_to_email = [child for child in partner.child_ids if child.move_type == 'invoice' and child.email]
            partners_to_email = [child for child in partner.child_ids if child.type == 'invoice' and child.email]
            if not partners_to_email and partner.email:
                partners_to_email = [partner]
            if partners_to_email:
                logging.warning("Partners to email is %s", partners_to_email)
                for partner_to_email in partners_to_email:
                    mail_template_id = self.env['ir.model.data']._xmlid_to_res_id(
                        'account_statement.email_template_customer_statement')
                    if mail_template_id:
                        logging.warning("Mail template ID is %s", mail_template_id)
                        mail_template = self.env['mail.template'].search([('id','=',mail_template_id)])
                        mail_template.send_mail(partner_to_email.id)
                if partner not in partner_to_email:
                    self.message_post([partner.id], body=_('Customer Statement email sent to %s' % ', '.join(
                        ['%s <%s>' % (partner.name, partner.email) for partner in partners_to_email])))
        return unknown_mails

    def supplier_send_mail(self):
        unknown_mails = 0
        for partner in self:
            partners_to_email = [child for child in partner.child_ids if child.move_type == 'invoice' and child.email]
            if not partners_to_email and partner.email:
                partners_to_email = [partner]
            if partners_to_email:
                for partner_to_email in partners_to_email:
                    mail_template_id = self.env['ir.model.data'].xmlid_to_object(
                        'account_statement.email_template_supplier_statement')
                    mail_template_id.send_mail(partner_to_email.id)
        # if partner not in partner_to_email:
        # self.message_post([partner.id], body=_('Customer Statement email sent to %s' % ', '.join(['%s <%s>' % (partner.name, partner.email) for partner in partners_to_email])))
        return unknown_mails

    def set_payment_lines(self):

        self.customer_payment_line_ids.unlink()
        self.customer_bal = 0
        payments = self.env['payments.statement.invoice']
        for inv in self.balance_invoice_ids:
            # These are all the customer invoices / vendor bills

            # if dates are supplied we only get a selection of invoices
            if self.customer_start and self.customer_end:
                # in this case we need to accumulate the balance of preceding invoices and store it
                if inv.invoice_date < self.customer_start:
                    self.customer_bal = self.customer_bal + inv.amount_total_signed
                if inv.invoice_date <= self.customer_end and inv.invoice_date >= self.customer_start:
                    payments.create({'date': inv.invoice_date,
                                     'invoice_number': inv.name,
                                     'account': self.property_account_receivable_id.code,
                                     'ref': inv.name,
                                     'invoices_debit': inv.amount_total_signed,
                                     'payments_credit': inv.credit_amount,
                                     'partner_id': self.id,
                                     'balance': inv.amount_total_signed - 0,

                                     })
            else:
                # if no dates are supplied - get all invoices
                payments.create({'date': inv.invoice_date,
                                 'invoice_number': inv.name,
                                 'account': self.property_account_receivable_id.code,
                                 'ref': inv.name,
                                 'invoices_debit': inv.amount_total_signed,
                                 'payments_credit': inv.credit_amount,
                                 'partner_id': self.id,
                                 'balance': inv.amount_total_signed - 0,

                                 })

        # here we are getting all payments for this customer
        payment_ids = self.env['account.payment'].search([('partner_id', '=', inv.partner_id.id)])

        for line in payment_ids:
            ref_line = ''

            if self.customer_start and self.customer_end:
                if line.date < self.customer_start:
                    # Here we need to subtract payments from the customer balance
                    self.customer_bal = self.customer_bal - line.amount
                if line.date <= self.customer_end and line.date >= self.customer_start:
                    if line.ref:
                        ref_line = 'Payment Ref: ' + line.name + ' \nInvoice Ref: ' + line.ref + ' \nAmount: ' + str(
                            line.amount)
                    else:
                        ref_line = 'Payment Ref: ' + line.name + ' \nAmount: ' + str(line.amount)
                    payments.create({'date': line.date,
                                     # 'invoice_number' : line.name +' : ' +  inv.name,
                                     'account': self.property_account_receivable_id.code,
                                     'ref': line.name,
                                     'invoices_debit': 0,
                                     'payments_credit': 0,
                                     'partner_id': self.id,
                                     'balance': 0,
                                     'line_amount': line.amount,
                                     'trans_type': 'payment',

                                     })

            else:
                # We dont subtract from the balance but get all payments
                if line.ref:
                    ref_line = 'Payment Ref: ' + line.name + ' \nInvoice Ref: ' + line.ref + ' \nAmount: ' + str(
                        line.amount)
                else:
                    ref_line = 'Payment Ref: ' + line.name + ' \nAmount: ' + str(line.amount)
                payments.create({'date': line.date,
                                 # 'invoice_number' : line.name +' : ' +  inv.name,
                                 'account': self.property_account_receivable_id.code,
                                 'ref': line.name,
                                 'invoices_debit': 0,
                                 'payments_credit': 0,
                                 'partner_id': self.id,
                                 'balance': 0 - line.amount,
                                 'line_amount': line.amount,
                                 'trans_type': 'payment',

                                 })

        return

    def set_payment_lines_vendors(self):
        self.vendor_bal = 0
        self.vendor_payment_line_ids.unlink()
        payments = self.env['payments.statement.invoice']

        print("ssssssssssssssssssssssssssssssss", self.supplier_invoice_ids)
        for inv in self.supplier_invoice_ids:
            if self.vendor_start and self.vendor_end:

                if inv.invoice_date < self.vendor_start:
                    print("awwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww", inv.name)
                    print("cccccccccccccccccccccccccccccccccc", -(inv.amount_total_signed))
                    self.vendor_bal = self.vendor_bal + -(inv.amount_total_signed)

                if inv.invoice_date >= self.vendor_start and inv.invoice_date <= self.vendor_end:
                    payments.create({'date': inv.invoice_date,
                                     'invoice_number': inv.name,
                                     'account': self.property_account_payable_id.code,
                                     'ref': inv.name,
                                     'invoices_debit': -(inv.amount_total_signed),
                                     'payments_credit': 0,
                                     'vendor_id': self.id,
                                     'balance': -(inv.amount_total_signed) - 0,

                                     })

            else:
                payments.create({'date': inv.invoice_date,
                                 'invoice_number': inv.name,
                                 'account': self.property_account_payable_id.code,
                                 'ref': inv.name,
                                 'invoices_debit': -(inv.amount_total_signed),
                                 'payments_credit': 0,
                                 'vendor_id': self.id,
                                 'balance': -(inv.amount_total_signed) - 0,

                                 })

            payment_ids = self.env['account.payment'].search([('ref', '=', inv.name)])

            for line in payment_ids:
                if self.vendor_start and self.vendor_end:

                    if line.date < self.vendor_start:
                        print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", -(line.amount))
                        self.vendor_bal = self.vendor_bal - line.amount

                    if line.date >= self.vendor_start and line.date <= self.vendor_end:
                        payments.create({'date': line.date,
                                         'invoice_number': line.name + ' : ' + inv.name,
                                         'account': self.property_account_payable_id.code,
                                         'ref': line.name + ' : ' + inv.name,
                                         'invoices_debit': 0,
                                         'payments_credit': line.amount,
                                         'vendor_id': self.id,
                                         'balance': 0 - line.amount,

                                         })

                else:

                    payments.create({'date': line.date,
                                     'invoice_number': line.name + ' : ' + inv.name,
                                     'account': self.property_account_payable_id.code,
                                     'ref': line.name + ' : ' + inv.name,
                                     'invoices_debit': 0,
                                     'payments_credit': line.amount,
                                     'vendor_id': self.id,
                                     'balance': 0 - line.amount,

                                     })

        return

    def do_button_print_statement(self):
        self.set_payment_lines()
        return self.env.ref('account_statement.report_customert_print').report_action(self)

    def do_button_print_statement_vendor(self):
        self.set_payment_lines_vendors()
        return self.env.ref('account_statement.report_supplier_print').report_action(self)
