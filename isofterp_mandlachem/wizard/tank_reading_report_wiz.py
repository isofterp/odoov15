from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime
import pandas as pd
from bokeh.plotting import figure, show

from bokeh.io import export_svgs
import svglib.svglib as svglib
from reportlab.graphics import renderPDF
import logging

class WizTankReading(models.TransientModel):
    _name = "tank.reading.wizard"
    _description = "Tank Reading Report"

    start_date = fields.Date(string="Start Date", default='2022-07-01')
    end_date = fields.Date(string="End Date", default=datetime.today())
    site_ids = fields.Many2many('site.site', string='Site')

    def run_report(self):
        df = self.get_report_data()
        """ So here we  have back all the consolidated data by line/tank"""
        """ We now need to find out which lines go to which people (Technician and Contacts. Load into recipient_df"""

        recipient_df = self._build_recipients(df)
        """ Now we have a DF (recipient_df)  with user_id and rec ids"""
        """ So create another df with for each email address"""
        self._build_email_data(recipient_df, df)

    def get_report_data(self):
        df = pd.DataFrame()
        site_obj = self.env['site.site']
        tank_reading_obj = self.env['tank.reading']
        tank_obj = self.env['site.tank']
        key = site = line = tank = date = qty = []
        delta = self.end_date - self.start_date
        no_days = delta.days + 1  # used to work out daily average
        #date_domain = [('date', '>=', self.start_date), ('date', '<=', self.end_date)]
        date_domain = [('date_last_reading', '>=', self.start_date), ('date_last_reading', '<=', self.end_date)]

        final_site_ids = self.site_ids.mapped("id")
        site_domain = []
        if self.site_ids:
            site_domain += [('id', 'in', final_site_ids)]
        i = 0
        for current_site in site_obj.search(site_domain):
            recs = tank_reading_obj.search([('site_id', '=', current_site.id)] + date_domain)
            if recs:
                for rec in recs:
                    if i == 0:
                        """ Create first record"""
                        df = pd.DataFrame({
                            'key': [rec.site_id.name + rec.tank_id.name],
                            'date': [rec.date.strftime("%Y-%m-%d")],
                            'site': [rec.site_id.name],
                            'site_id': [rec.site_id.id],
                            'line': [rec.line_id.name],
                            'line_id': [rec.line_id.id],
                            'tank': [rec.tank_id.name],
                            'tank_id': [rec.tank_id.id],
                            'tank_bal': [0],
                            'qty': [rec.usage]
                        }, index=['key'])
                    else:

                        if not rec.site_id.name or not rec.tank_id.name:
                            continue
                        index = df.index[(df['key'] == rec.site_id.name + rec.tank_id.name)].tolist()
                        if index:
                            """ we have found a record match so update the qty"""
                            df.at[index, 'qty'] = df['qty'] + rec.usage
                        else:
                            """ we have NOT found a record so create a new one"""
                            #logging.warning("Site name %s and tank name %s", rec.site_id.name, rec.tank_id.name)

                            df = df.append({
                                'key': rec.site_id.name + rec.tank_id.name,
                                'date': rec.date.strftime("%Y-%m-%d"),
                                'site': rec.site_id.name,
                                'site_id': rec.site_id.id,
                                'line': rec.line_id.name,
                                'line_id': rec.line_id.id,
                                'tank': rec.tank_id.name,
                                'tank_id': rec.tank_id.id,
                                'tank_bal': 0,
                                'qty': rec.usage
                            }, ignore_index=True)

                    i += 1

            """ Finished with a Site so call email function """
            report_data = df.to_dict(orient='records')
            """  send this Site's data and send it using email_dict"""
            """ reset i and clear the dataframe and email dictionary for next branch """
            # i = 0
            # email_dict = []
            # df.drop(columns=[i for i in df.columns])

        if df.empty:  # no data found
            return
        # Set the daily average
        df['qty'] = df['qty'] / no_days

        # look up tank balance for each tank
        for index, row in df.iterrows():
            tank = tank_obj.search([('site_id', '=', row["site_id"]),('name', '=', row["tank"])])
            if tank:
                df.at[index,'tank_bal'] = tank.tank_balance
        return df

    def _build_recipients(self, df):
        # if not df:
        #     return
        line_obj = self.env['site.line']
        column_names = ["user_name",  "user_id", "site_id", "df_index"]
        recipient_df = pd.DataFrame(columns=column_names)
        """ Create a DF with user name,user id and rec id of df"""

        for index, row in df.iterrows():
            #line = line_obj.search([('name', '=', row["line"])])
            line = line_obj.search([('name', '=', row["line"]), ('site_id', '=', row["site_id"])])
            for x in line.employee_ids:
                recipient_df = recipient_df.append({
                    'user_name': x.user_id.name,
                    'user_id': x.user_id.partner_id.email,
                    'site_id': line.site_id.id,
                    'df_index': index,
                }, ignore_index=True)
            for x in line.contact_ids:
                recipient_df = recipient_df.append({
                    'user_name': x.name,
                    'user_id': x.email,
                    'site_id': line.site_id.id,
                    'df_index': index,
                }, ignore_index=True)
        recipient_df.sort_values(by=['user_id', 'df_index'], inplace=True)
        return recipient_df

    def _build_email_data(self, recipient_df, df):
        # if not recipient_df:
        #     return
        column_names = ["key", "date", "site", "site_id", "line", "line_id", "tank","tank_id", "tank_bal", "qty"]
        email_data_lines_df = pd.DataFrame(columns=column_names)
        previous_user = 'first'
        previous_site = 'first'
        current_user = current_site = ''
        for index, row in recipient_df.iterrows():
            current_user = row['user_id']
            current_site = row['site_id']
            if previous_user == 'first':
                previous_user = row['user_id']
            if current_user != previous_user:
                # change of email so send data and start on the next email
                # Send data on change of site_id

                self._send_report(previous_user,email_data_lines_df)  # Send after reaching the last record in the for loop
                current_user = previous_user = row['user_id']
                email_data_lines_df = pd.DataFrame(columns=column_names)  # Clear out the Dataframe
                email_data_lines_df.loc[len(email_data_lines_df)] = df.loc[row['df_index']]  #add the new record to fresh DF
            else:
                if previous_site == 'first':
                    previous_site = row['site_id']
                if current_site != previous_site:
                    self._send_report(current_user,
                                      email_data_lines_df)  # Send after reaching the last record in the for loop
                    current_site = previous_site = row['site_id']
                    email_data_lines_df = pd.DataFrame(columns=column_names)  # Clear out the Dataframe
                    email_data_lines_df.loc[len(email_data_lines_df)] = df.loc[
                        row['df_index']]  # add the new record to fresh DF
                else:
                    email_data_lines_df.loc[len(email_data_lines_df)] = df.loc[row['df_index']]  # copy the row out the original df to the email df
        self._send_report(previous_user, email_data_lines_df)  # Send after reaching the last record in the for loop

    def _send_report(self, user_id, email_data_lines_df):
        report_data = email_data_lines_df.to_dict(orient='records')
        #logging.warning("Email data @186 %s", report_data)
        email_body = ''
        email_to = ''

        mail_template_id = self.env['mail.template'].search([('name', '=', "Tank Usage Report")])
        str_intro = '<p style="font-size:14px;font-family:Raleway">Dear Customer,</p></br>'

        site_id = self.env['site.site'].search([('id','=',report_data[0].get('site_id'))])
        partner_id = self.env['res.partner'].search([('id', '=', site_id.partner_id.id)])
        str_comp = '<p style="font-size:14px;font-family:Raleway">Client :' + partner_id.name + '</p>'
        str_site_decr = '<p style="font-size:14px;font-family:Raleway">Site Description :' + report_data[0].get('site') + '</p>'
        str_date_start = '<p style="font-size:14px;font-family:Raleway">Date from :' + str(self.start_date) + '</p>'
        str_date_end = '<p style="font-size:14px;font-family:Raleway">Date to :' + str(self.end_date) + '</p></br>'
        str_report_url = '<p style="font-size:14px;font-family:Raleway">Please click on a link below to view the report for the tank.</p></br>'

        table_start = '<table class="table table-condensed" ' \
                      'style="width:120px;font-size:14px;font-family:Raleway;border-style:solid;margin:0 0 18px 0;border-left-color:rgb(221, 221, 221);' \
                      'border-bottom-color:rgb(221, 221, 221);border-right-color:rgb(221, 221, 221);' \
                      'border-top-color:rgb(221, 221, 221);border-left-width:1px;border-bottom-width:1px;' \
                      'border-right-width:1px;border-top-width:1px;max-width:100%;' \
                      'width:100%;background-color:transparent;border-collapse:collapse;">' \
                      '<thead style="background-color:#606060;color:#FFFFFF" >' \
                      '<tr><td>Line</td><td>Tank</td><td>Average Daily Usage</td><td>Stock level</td><td>Link</td></tr></thead>' \
                      '<tbody class="invoice_tbody">'

        email_body += str_intro
        email_body += str_comp
        email_body += str_site_decr
        email_body += str_date_start
        email_body += str_date_end
        email_body += str_report_url
        email_body += table_start

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        report_function = 'site/tank_readings'



        # The report data will go here
        for line in report_data:
            report_params = 'from_date=' + str(self.start_date) + '&to_date=' + str(self.end_date) + '&site_id=' + \
                            str(line.get('site_id')) + '&line_id=' + str(line.get('line_id')) + '&tank_id=' + str(line.get('tank_id'))
            chart_link = base_url + '/' + report_function + '?'
            url_link = "<a href=" + chart_link + report_params + " '</a>Click to view Chart"
            #email_body += "<a href = copytype-billing.isofterp.co.za/my/contracts/?id=" + line.analytic_account_id.code + " </a>Click to capture readings"
            # email_body += "<div style = 'text-align: center; margin: 16px 0px 16px 0px;' >"
            # email_body += "<a href = copytype-billing.isofterp.co.za/my/contracts/?id=" + line.analytic_account_id.code + " </a>Click to capture readings"
            # email_body += "</div>"
            format_avg_qty = "{:.2f}".format(line.get('qty'))
            format_tank_bal = "{:.2f}".format(line.get('tank_bal'))
            email_body += "<tr>" \
                          "<td>" + line.get('line') + "</td>" + \
                          "<td>" + line.get('tank') + "</td>" + \
                          "<td>" + str(format_avg_qty) + "</td>" + \
                          "<td>" + str(format_tank_bal) + "</td>" + \
                          "<td>" + url_link + "</td></tr>"

        table_end = '</tbody></table>'
        email_body += table_end
        email_body += '<br> <p style="font-size:14px;font-family:Raleway"> Kind regards,</p><p style="font-size:14px;font-family:Raleway">The Mandlachem SA Team</p>'
        mail_values = {
            'email_from': mail_template_id.email_from,
            'email_to': user_id,
            'subject': mail_template_id.subject,
            'body_html': email_body,
            'state': 'outgoing',
        }
        self.env['mail.mail'].sudo().create(mail_values)

