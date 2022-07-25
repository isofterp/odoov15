from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime
import pandas as pd
#from bokeh.plotting import figure, show

class WizTankReading(models.TransientModel):
    _name = "tank.reading.wizard"
    _description = "Tank Reading Report"

    start_date = fields.Date(string="Start Date", default='2022-07-01')
    end_date = fields.Date(string="End Date", default=datetime.today())
    site_ids = fields.Many2many('site.site', string='Site')

    def run_report(self):
        df = pd.DataFrame()
        key = site = line = tank = date = qty = []
        delta = self.end_date - self.start_date
        no_days = delta.days + 1  # used to work out daily average
        domain = [('date','>=',self.start_date),('date','<=',self.end_date)]
        print(self.site_ids)
        final_site_ids = self.site_ids.mapped("id")
        if self.site_ids:
            domain += [('site_id', 'in', final_site_ids)]
        i = 0
        print(domain)
        for rec in self.env['tank.reading'].search(domain, order='site_id, tank_id'):
            if i == 0:
                df = pd.DataFrame({
                    'key': [rec.site_id.name + rec.tank_id.name],
                    'date': [rec.date.strftime("%Y-%m-%d")],
                    'site': [rec.site_id.name],
                    'line': [rec.line_id.name],
                    'tank': [rec.tank_id.name],
                    'qty': [rec.usage]
                }, index=['key'])
            else:

                # found  = df.loc[(df['site'] == rec.site_id.name)].any().index()
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
                        'tank': rec.tank_id.name,
                        'qty': rec.usage
                    }, ignore_index=True)
            i += 1
        print("*****Finished creating DF*********",)
        if df.empty:  # no data found
            return
        print(no_days,i)
        df['qty'] = df['qty'] / no_days
        print(df)

   