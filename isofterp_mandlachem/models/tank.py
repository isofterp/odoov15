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
        #print('in check_min_bal')
        if self.last_actual_reading:
            if self.last_actual_reading <= self.min:
                self.last_notes = "Replenish"
                #print('in check_min_bal', self.last_notes)
            if self.last_notes != 'Replenish':
                self.last_notes = ''
        self.date_last_capture = datetime.today()
        self.date_last_reading = datetime.today()
        self.usage = 0
        return

    def write(self, vals):
        # If one of these fields then user is just amending static Tank data so no need to create reading Trx
        if vals.get('name') or vals.get('min') or  vals.get('max'):
            return super(SiteTank, self).write(vals)

        #print('in tank write', vals)
        if vals.get('date_last_reading'):
            date_last_reading = vals['date_last_reading']
            #print("date_last_reading=",date_last_reading)
        else:
            date_last_reading = datetime.today()

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
                self.usage_min = usage
            if usage > self.usage_max or self.usage_max == 0:
                self.usage_max = usage
        else:
            usage = 0

        transaction_vals = {
            'line_id': self.line_id.id,
            'site_id': self.site_id.id,
            'tank_id': self.id,
            'date_last_reading': date_last_reading,
            'theoretical_usage': self.tank_balance - last_reading,
            'actual_reading': last_reading,
            'usage': usage,
            'narrative': last_note
        }
        # print('about to create trx reading',vals['tank_balance'],vals['last_actual_reading'])
        self.env['tank.reading'].create(transaction_vals)
        if vals.get('last_actual_reading'):
            vals['tank_balance'] = vals['last_actual_reading']
        vals['date_last_capture'] = datetime.today()
        return super(SiteTank, self).write(vals)

    name = fields.Char("Tank Name")
    branch_id = fields.Many2one(related='site_id.branch_id', string="Branch")
    line_id = fields.Many2one('site.line', string='Lines', required=True)
    site_id = fields.Many2one('site.site', string='Site', required=True)
    tank_reading_ids = fields.One2many('tank.reading', 'tank_id', string='Lines')
    min = fields.Float('Min')
    usage_min = fields.Float('Usage Min')
    max = fields.Float('Max')
    usage_max = fields.Float('Usage Max')
    date_last_capture = fields.Date('Date', default=datetime.today())
    date_last_reading = fields.Date('Date', default=datetime.today())
    tank_balance = fields.Float('Tank Balance')
    last_actual_reading = fields.Float('Tank Balance')
    last_notes = fields.Text('Notes')
    usage = fields.Float('Usage')


class SiteTankReading(models.Model):
    _name = 'tank.reading'
    _description = 'Tank Readings'
    _order = 'date desc'

    #file_path = tempfile.mktemp(suffix='.xlsx')
    """ Set up the columns for the dataframe """
    key = site = line = tank = date = qty = []

    def action_create_usage_report(self):
        df = pd.DataFrame()
        #print(self.env.context)
        i = 0
        high_date = low_date = ''
        for rec in self.browse(self.env.context.get('active_ids')):
            if i == 0:
                """ Create the first record """
                low_date = rec.date.strftime("%Y-%m-%d")
                high_date = rec.date.strftime("%Y-%m-%d")
                df = pd.DataFrame({
                    'key': [rec.site_id.name + rec.tank_id.name],
                    'date': [rec.date.strftime("%Y-%m-%d")],
                    'site': [rec.site_id.name],
                    'line': [rec.line_id.name],
                    'tank': [rec.tank_id.name],
                    'qty': [rec.usage]
                },index=['key'])
            else:
                #print('else i <> 0',i)
                #found  = df.loc[(df['site'] == rec.site_id.name)].any().index()
                if rec.date.strftime("%Y-%m-%d") < low_date:
                    low_date = rec.date.strftime("%Y-%m-%d")
                if rec.date.strftime("%Y-%m-%d") > high_date:
                    high_date = rec.date.strftime("%Y-%m-%d")
                index = df.index[(df['key'] == rec.site_id.name + rec.tank_id.name)].tolist()
                if index:
                    """ we have found a record match so update the qty"""
                    df.at[index, 'qty'] = df['qty'] + rec.usage
                else:
                    """ we have NOT found a record so create a new one"""
                    df = df.append({
                        'key': rec.site_id.name + rec.tank_id.name,
                        'date': rec.date.strftime("%Y-%m-%d"),
                        'site': rec.site_id.name,
                        'line': rec.line_id.name,
                        'tank':rec.tank_id.name,
                        'qty': rec.usage
                    }, ignore_index=True)
            i += 1
        #print("*****Finished creating DF*********")
        #print(df)
        """ work out the number of days between highest and lowest dates"""
        high_date_obj = datetime.strptime(high_date,"%Y-%m-%d")
        low_date_obj = datetime.strptime(low_date, "%Y-%m-%d")
        delta =  high_date_obj - low_date_obj
        i = delta.days + 1
        """ devide the total qty by number of days to get average daily"""
        df['qty'] = df['qty']/i
        """Now add a record to the dataframe for low date and high date (to be used in report header)"""
        df.loc[-1] = ['High Date', high_date, '', '', '', '']  # adding a row
        df.index = df.index + 1  # shifting index
        df.sort_index(inplace=True)
        df.loc[-1] = ['Low Date', low_date,'','','','']  # adding a row
        df.index = df.index + 1  # shifting index
        df.sort_index(inplace=True)
        print(df)
        my_dict = df.to_dict('records')
        #print(my_dict)

        return

    name = fields.Char("Tank Name")
    branch_id = fields.Many2one(related='site_id.branch_id', string="Branch")
    line_id = fields.Many2one('site.line', string='Lines')
    site_id = fields.Many2one('site.site', string='Site')
    tank_id = fields.Many2one("site.tank", string="Tanks")
    actual_reading = fields.Float('Tank Balance')
    date = fields.Datetime('Capture Date',  default=datetime.today())
    date_last_reading = fields.Datetime('Reading date')
    theoretical_usage = fields.Float('Theoretical Usage')
    usage = fields.Float('Usage')
    narrative = fields.Text("Description")
