import json
from datetime import date
from random import randint


from datetime import datetime,timedelta
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape
from bokeh.plotting import figure, show
from bokeh.models import Span
from bokeh.models import BoxAnnotation
from bokeh.models import HoverTool
from bokeh.models import ColumnDataSource, DatetimeTickFormatter,  Row, Column,FixedTicker,HoverTool,DataTable, DateFormatter, TableColumn
from bokeh.resources import CDN
from bokeh.embed import file_html


import pandas as pd
#http://localhost:8014/site/tank_readings?from_date=2022-07-01&to_date=2022-07-25&site_id=14&line_id=7&tank_id=9


class draw_graph(http.Controller):
    #@http.route('/site/tank_readings', auth='none', type="json", )
    @http.route('/site/tank_readings', auth='none', type="http", )
    def create_graph(self, **args):
        vals = {}
        for key in args.keys():
            vals[key] = args[key]
        #print('28',vals['from_date'])
        start_date = datetime.strptime(vals['from_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(vals['to_date'], '%Y-%m-%d').date()
        delta = end_date - start_date
        no_days = delta.days + 1  # used to work out daily average
        x_date = []
        usage = []
        my_tickers = []
        first_date = datetime.strptime(vals['from_date'], '%Y-%m-%d')  # print(x_date[0])
        for i, v in enumerate(range(no_days)):
            x_date.append(first_date.strftime("%Y-%m-%d"))
            first_date = first_date + timedelta(days=1)
            usage.append(0)
            my_tickers.append(i)
        site = request.env['site.site'].search([('id','=',int(vals['site_id']))])
        line = request.env['site.line'].search([('id', '=', vals['line_id'])])
        tank = request.env['site.tank'].search([('id', '=', vals['tank_id'])])
        y_min = tank.min
        y_max = tank.max
        max_label = "Max=" + str(y_max)
        min_label = "Min=" + str(y_min)
        domain = [('site_id', '=', int(vals['site_id'])),
                  ('line_id', '=',  int(vals['line_id'])),
                  ('tank_id', '=', int(vals['tank_id'])),
                  ('date', '>=', start_date), ('date', '<=', end_date)]
        tank_readings = request.env['tank.reading'].search(domain)
        average_usage = 0
        note = []
        dates = []
        for reading in tank_readings:
            x = x_date.index(reading.date.strftime("%Y-%m-%d"))
            usage[x] += reading.usage
            average_usage += reading.usage
            dates.append(reading.date)              #This is used later to build DataTabe
            note.append(reading.narrative)          #This is used later to build DataTabe
        average_usage = round(average_usage/no_days,2)    # get daily average
        ave_label = "Daily Ave " + str(average_usage)

        """ ****************  start defining plot ******************    """
        header = ("USAGE ANALYSIS REPORT\nFrom {} To {} ,".format(start_date, end_date))
        header += ('   Site {},    Line {}  Tank {}'.format(site.name, line.name, tank.name))
       # This was when we used Pandas to create the Plot data
       # df = pd.DataFrame(data={
        #     'string_date': x_date,
        #     'usage': usage
        #     })
        # source = ColumnDataSource(df)

        # Format the tooltip
        tooltips = [
            ('Usage', '@top'),
        ]
        """ Path to MandlaChem Logo o their website"""
        path = "https://static.wixstatic.com/media/8eca0d_49d47e53e4a848b6b38c1028d7dfef18~mv2.png/v1/fill/w_446,h_196,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/MCSA%20Trans.png"
        p = figure(title=header,  y_axis_label="Volume",
                   toolbar_location="above",
                   width=1100,
                   height=550,
                   )
        p.title.text_font = 'Raleway'
        p.toolbar.logo = None
        p.add_tools(HoverTool(tooltips=tooltips))
        p.image_url(url=[path], x=len(usage) - 8, y=max(usage) + 30, w=5.8, h=30.6)  # Position the logo
        p.ray(x=[0], y=y_max, length=0, color="red", angle=0, line_width=3, line_dash="dotdash",legend_label=max_label)
        p.ray(x=[0], y=y_min, length=0, color="green", angle=0, line_width=3, line_dash="dashed",legend_label=min_label)
        p.ray(x=[0], y=average_usage, length=0, color="orange", angle=0, line_width=3, line_dash="dashdot",legend_label=ave_label)
        p.xaxis.major_label_overrides = {
            i: date for i, date in enumerate(x_date)
        }
        p.xaxis[0].ticker = FixedTicker(ticks=my_tickers)
        p.xaxis.major_label_orientation = 3.4142 / 4    # """ This orientates the date on its side """
        p.vbar( x=my_tickers, top=usage, width=0.5, legend_label="Usage", color='blue')
        p.legend.label_text_font = "Raleway"
        p.legend.location = "top_left"
        """ Set up data for DataTable"""
        data = dict(
            dates=dates,
            notes=note,
        )
        source = ColumnDataSource(data)
        columns = [
            TableColumn(field="dates", title="Date", formatter=DateFormatter()),
            TableColumn(field="notes", title="Notes"),
        ]
        data_table = DataTable(source=source, columns=columns, width=400, height=280)
        string = file_html(Column(Row(p), Row(data_table)), CDN, "Tank Usage Report")
        return string


