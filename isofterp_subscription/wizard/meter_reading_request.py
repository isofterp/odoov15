# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime
import logging


class MeterReadingRequestWizard(models.TransientModel):
    _name = 'meter.reading.request.wizard'
    _description = 'Meter Reading Request Wizard'

    def cron_meter_reading_bulk_mail(self, context=None):
        message_0 = "Could you please fill in the latest meter reading figures for the following:"
        message_1 = "This is your second reminder to enter your meter readings"
        message_2 = "This is your FINAL reminder to enter your meter readings"
        logging.warning("----- Cron Meter reading running")
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
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        logging.warning("Base Url is %s", base_url)
        #print(err)
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
                #email_body += "<a href = /my/contracts/?id=" + line.analytic_account_id.code + " </a>Click to capture readings"
                email_body += "<a href =" + base_url + "/my/contracts/?id=" + line.analytic_account_id.code + " </a>Click to capture readings"
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
            #email_body += "<a href = /my/contracts/?id=" + line.analytic_account_id.code + " </a>Click to capture readings"
            email_body += "<a href =" + base_url + "/my/contracts/?id=" + line.analytic_account_id.code + " </a>Click to capture readings"
            email_body += "</div>"

            email_to = 'sue@copytype.co.za'  ################   !!!!!!!!!!!   Testing email address - remove to go live  !!!!!
            email_to = 'edgar@isoft.co.za'
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
            #if line.analytic_account_id.code == '11104580':
            #self.message_post(
            #    body=" THIS needs to change for go live " + email_body + " THIS needs to change for go live ")
            mail_out = mail.create(mail_values)
            # mail.send(mail_out)
            line.x_email_count += 1

    def run_meter_reading_bulk_request(self, context=None):
        # Sion has requested that emails must be generated per responsible person and not for every machine
        # So what is the process
        # For each sub line extract the person
        # Check if this person is already in a list of contacts
        # if the person is get the sub_lines and add the new line
        # Else create a new header and sub_line
        mail_list = []
        machine_list = []
        temp_list = []
        machine_dict = {}
        recipient_dict = {}
        recipient = {}
        message_0 = "Could you please fill in the latest meter reading figures for the following:"
        message_1 = "This is your second reminder to enter your meter readings"
        message_2 = "This is your FINAL reminder to enter your meter readings"
        logging.warning("----- Cron Meter reading running")
        line_ids = self.env['sale.subscription.line'].search(['|', ('name', '=', 'Black copies'),
                                                              ('name', '=', 'Colour copies'),
                                                              ('quantity', '=', 0)])
        if line_ids:
            logging.warning("Line IDS were found %s", len(line_ids))
        else:
            logging.warning("No line ids were found")
            return
        email_subject = 'Meter Reading Inputs Required for ' + self.env.user.company_id.name
        mail = self.env['mail.mail']
        res_user_obj = self.env['res.users']
        user_id = res_user_obj.browse(self.env.context.get('uid'))
        email_from = user_id.partner_id.email
        email_to = ''
        previous_serial_number = ''
        for line in line_ids:
            temp_list = []
            email_to = line.x_serial_number_id.x_dlv_id.email
            if not email_to:
                continue
            if email_to not in recipient_dict.values():
                logging.warning("Could not find an email address")
                recipient = {
                    'email_to': email_to,
                }
                machine_dict = {
                    'serial': line.x_serial_number_id.name or 'No Serial',
                    'product': line.x_serial_number_id.product_id.name or 'No product',
                    'contract': line.analytic_account_id.code,
                }
                temp_list.append(machine_dict)
                recipient.update({'machine':temp_list})


                recipient_dict.update(recipient)

                #logging.warning("recipient_dict %s", recipient_dict)

            else:
                machine_dict = {
                    'serial': line.x_serial_number_id.name or 'No Serial',
                    'product': line.x_serial_number_id.product_id.name or 'No product',
                    'contract': line.analytic_account_id.code,
                }
                temp_list.append(machine_dict)
                recipient.update({'machine': temp_list})

                recipient_dict.update(recipient)

            mail_list.append(recipient)
        for email_list in mail_list:
            logging.warning("Mail list is %s", email_list)
        # for line in line_ids:
        #     serial_number = line.x_serial_number_id.name
        #     if not serial_number:
        #         serial_number = "No Serial"
        #     if serial_number == previous_serial_number: continue
        #     previous_serial_number = serial_number
        #     product = line.x_serial_number_id.product_id.name
        #     if not product:
        #         product = "No product"
        #     email_person = ''
        #     if line.x_serial_number_id.x_dlv_id.email:  # If the machine has an email  address use it
        #         email_to = line.x_serial_number_id.x_dlv_id.email
        #         email_person = line.x_serial_number_id.x_dlv_id.name
        #     else:  # send am email to the Company warning of no email address
        #         print("no email")
        #         email_body = "<div>This Contract: " + line.analytic_account_id.code + " has no email address. </br>Please phone " + line.analytic_account_id.partner_id.name
        #         email_body += " on " + line.analytic_account_id.partner_id.phone + " and enter the last meter readings for "
        #         email_body += "</br>" + product + " Serial Number: " + serial_number + "</div>"
        #         email_body += "<div style = 'text-align: center; margin: 16px 0px 16px 0px;' >"
        #         email_body += "<a href = /my/contracts/?id=" + line.analytic_account_id.code + " </a>Click to capture readings"
        #         email_body += "</div>"
        #         mail_values = {
        #             'email_from': email_from,
        #             'email_to': email_from,
        #             'subject': "WARNING from the  Meter Reading Email System",
        #             'body_html': email_body,
        #             'state': 'outgoing',
        #             'scheduled_date': datetime.now(),
        #         }
        #         # print("Mail values are %s", mail_values)
        #         if line.analytic_account_id.code == '11104580':
        #             # if line.analytic_account_id.partner_id.id == 186:  # KaapAgrie
        #             self.message_post(body=email_body)
        #             mail_out = mail.create(mail_values)
        #             # mail.send(mail_out)
        #             continue
        #     if line.x_email_count == 0:
        #         message = message_0
        #     else:
        #         if line.x_email_count == 1:
        #             message = message_1
        #         else:
        #             message = message_2
        #
        #     email_body = "<div>Good day&nbsp; " + email_person + ',<div><br></div><div>' + message + '<br/>' + 'Machine: ' + product \
        #                  + "<br/> Serial Number: " + serial_number + " <br/>Contract Number: " + line.analytic_account_id.code + "</div>"
        #     # !!!!!!!!! take the follwing line out after teting !!!!!!!!!!!!!!!!!!!!!!!!!!
        #     email_body += "<div> FOR TESTING - the real email address for " + email_person + " is " + email_to
        #     email_body += "<div style = 'text-align: center; margin: 16px 0px 16px 0px;' >"
        #     email_body += "<a href = /my/contracts/?id=" + line.analytic_account_id.code + " </a>Click to capture readings"
        #     email_body += "</div>"
        #
        #     email_to = 'sue@copytype.co.za'  ################   !!!!!!!!!!!   Testing email address - remove to go live  !!!!!
        #     email_to = 'edgar@isoft.co.za'
        #     mail_values = {
        #         'email_from': email_from,
        #         'email_to': email_to,
        #         'subject': email_subject,
        #         'body_html': email_body,
        #         'state': 'outgoing',
        #         'scheduled_date': datetime.now(),
        #     }
        #     if mail_values:
        #         logging.warning("Mail values %s", mail_values)
        #     else:
        #         logging.warning("No email values were generated!!!")
        #     # print(mail_values)
        #
        #     # if line.analytic_account_id.partner_id.id == 186:  # KaapAgrie
        #     # print("we are here at last", line.analytic_account_id.partner_id.id)
        #     #if line.analytic_account_id.code == '11104580':
        #     #self.message_post(
        #     #    body=" THIS needs to change for go live " + email_body + " THIS needs to change for go live ")
        #     mail_out = mail.create(mail_values)
        #     # mail.send(mail_out)
        #     line.x_email_count += 1