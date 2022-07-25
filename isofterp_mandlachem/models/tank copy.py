# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import base64
import pandas as pd
import tempfile
import xlsxwriter


class SiteTank(models.Model):
    _name = 'site.tank'
    _description = 'Tanks'

    @api.onchange('last_actual_reading')
    def check_min_bal(self):
        print('in check_min_bal')
        if self.last_actual_reading:
            if self.last_actual_reading <= self.min:
                self.last_notes = "Replenish"
                print('in check_min_bal', self.last_notes)
            if self.last_notes != 'Replenish':
                self.last_notes = ''
            return

    def write(self, vals):
        print('in tank write', vals)
        if vals.get('last_actual_reading'):
            last_reading = vals['last_actual_reading']
        else:
            last_reading = 0
        if vals.get('last_notes'):
            last_note = vals['last_notes']
        else:
            last_note = ''
        if vals.get('usage'):
            usage = vals['usage']
            if usage < self.usage_min or self.usage_min == 0:
                print('here')
                self.usage_min = usage
            if usage > self.usage_max or self.usage_max == 0:
                print('here1')
                self.usage_max = usage
        else:
            usage = 0

        transaction_vals = {
            'line_id': self.line_id.id,
            'site_id': self.site_id.id,
            'tank_id': self.id,
            'theoretical_usage': self.tank_balance - last_reading,
            'actual_reading': last_reading,
            'usage': usage,
            'narrative': self.last_notes
        }
        if vals.get('last_actual_reading'):
            # print('about to create trx reading',vals['tank_balance'],vals['last_actual_reading'])
            self.env['tank.reading'].create(transaction_vals)
            vals['tank_balance'] = vals['last_actual_reading']
        # vals['last_actual_reading'] = 0
        # vals['usage'] = 0

        return super(SiteTank, self).write(vals)

    name = fields.Char("Tank Name")
    line_id = fields.Many2one('site.line', string='Lines')
    site_id = fields.Many2one('site.site', string='Site')
    branch_id = fields.Many2one(related='site_id', string="Branch")
    tank_reading_ids = fields.One2many('tank.reading', 'tank_id', string='Lines')
    min = fields.Float('Min')
    usage_min = fields.Float('Usage Min')
    max = fields.Float('Max')
    usage_max = fields.Float('Usage Max')
    tank_balance = fields.Float('Tank Balance')
    last_actual_reading = fields.Float('Last Actual Reading', )
    last_notes = fields.Char('Notes')
    usage = fields.Float('Usage')


class SiteTankReading(models.Model):
    _name = 'tank.reading'
    _description = 'Tank Readings'
    _order = 'line_id, create_date desc'

    def action_create_usage_report(self):



    # @api.model
    # def create(self, vals):
    #     tank = self.env['site.tank'].search([('id', '=', vals.get('tank_id'))])
    #     print(tank.tank_balance,tank.name)
    #     print(vals.get('tank_balance') , tank.tank_balance,tank.id)
    #     vals['theoretical_usage'] = vals.get('tank_balance') - tank.tank_balance
    #     tank.tank_balance = vals.get('tank_balance')
    #     return super(SiteTankReading, self).create(vals)

    # def write(self, vals):
    #     # print(vals)
    #     self.tank_id.tank_balance = vals.get('tank_balance')
    #     vals['theoretical_usage'] = self.tank_balance - self.tank_id.tank_balance
    #     return super(SiteTankReading, self).write(vals)

    # @api.onchange('tank_balance')
    # def _update_tank_balance(self):
    #     if self.tank_balance:
    #         if self.tank_balance <= self.tank_id.min:
    #             self.narrative = "Replenish"  # This causes a warning message to fire in the form
    #
    #
    #

    # def action_create_usage_report(self):
        # print('we are in action_create_usage_report', self.env.context.get('active_ids'))
        # dict = {}
        # i = 1
        # for rec in self.browse(self.env.context.get('active_ids')):
        #     print('we are here', rec.site_id.name, " ", i)
        #     # print("@114",dict,dict.items(),len(dict))
        #     if rec.site_id.name in dict:
        #         print('site found ', dict[rec.site_id.name])
        #         if rec.line_id.name == dict[rec.site_id.name]['lines']['name']:
        #             print('found Line',)
        #             print(dict[rec.site_id.name]['lines']['tanks'])
        #             print(dict[rec.site_id.name]['lines'])
        #             # if rec.tank_id.name == dict[rec.site_id.name]['lines']['tanks']['name']:
        #             #     print('found Tanks')
        #             #
        #             #     dict[rec.site_id.name]['lines']['tanks'] = {'name': rec.tank_id.name, 'qyt': rec.usage}
        #             print(dict)
        #
        #         else:
        #             print(' NOT found Line')
        #             dict[rec.site_id.name]['line'] = rec.line_id.name
        #         dict[rec.site_id.name]['lines']['tanks'] = {'name': rec.tank_id.name, 'qyt': rec.usage}
        #     # if rec.line_id.name in dict.values():
        #     else:
        #         print('site NOT found ')
        #         dict[rec.site_id.name] = {}
        #         dict[rec.site_id.name]['lines'] = {}
        #         dict[rec.site_id.name]['lines']['name'] = rec.line_id.name
        #         #print('so far1', dict)
        #         dict[rec.site_id.name]['lines']['tanks'] = {}
        #         #print('so far2', dict)
        #         dict[rec.site_id.name]['lines']['tanks'] = {'name': rec.tank_id.name,'qyt': rec.usage }
        #         print('so far3', dict)
        #         #dict[rec.site_id.name][rec.line_id.name][rec.tank_id.name]['qty'] = rec.usage
        # print(dict)
        # i += 1
        #
        # print('new dict ', dict)
        #

        # for contact in line.line_id.contact_ids:
        #     print(contact.name)
        # for emp in line.line_id.employee_ids:
        #     print(emp.work_email)

        # for line in self.browse(self.env.context.get('active_ids')):
        #     data = {'site': 'Roly Site'}
        #     pdf = self.env.ref("isofterp_mandlachem.action_report_usage")._render_qweb_pdf(self.id, data=data)
        #     data_record = base64.b64encode(pdf[0])
        #     ir_values = {
        #         'name': "Tank Usage Report.pdf",
        #         'type': 'binary',
        #         'datas': data_record,
        #         'store_fname': data_record,
        #         'mimetype': 'application/x-pdf',
        #     }
        #
        #     data_id = self.env['ir.attachment'].create(ir_values)
        #     template = self.env['mail.template'].search([('name', '=', 'Tank Usage Report')])
        #     if template:
        #         print("Template is %s", template.name)
        #     else:
        #         print("Could not find the template")
        #
        #     template.attachment_ids = [(6, 0, [data_id.id])]
        #     partner = self.env['res.partner'].search([('id', '=', 7)])
        #     email_values = {'email_to': partner.email, }
        #     template.with_context(email_values).send_mail(7, email_values=email_values, force_send=False)
        #     template.attachment_ids = [(3, data_id.id)]
        #     return True


    # print('DATA=',self.env.ref(
    #     "isofterp_mandlachem.action_report_usage"
    # ).report_action(self.env.context.get('active_ids'), data=data))
    # return self.env.ref(
    #     "isofterp_mandlachem.action_report_usage"
    # ).report_action(self.env.context.get('active_ids'), data=data)


    name = fields.Char("Tank Name")
    line_id = fields.Many2one('site.line', string='Lines')
    site_id = fields.Many2one('site.site', string='Site')
    tank_id = fields.Many2one("site.tank", string="Tanks")
    actual_reading = fields.Float('Actual Reading')
    date = fields.Datetime('Date', default=datetime.today())
    theoretical_usage = fields.Float('Theoretical Usage')
    usage = fields.Float('Usage')
    narrative = fields.Char("Description")
