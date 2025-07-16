import json
from datetime import date
from random import randint
from collections import OrderedDict # For python 2.7 and above


from datetime import datetime,timedelta
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape
from bokeh.plotting import figure, show
from bokeh.models import Span, Div
from bokeh.models import BoxAnnotation
from bokeh.models import HoverTool,NumeralTickFormatter,ImageURL
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
                  ('line_id', '=', int(vals['line_id'])),
                  ('tank_id', '=', int(vals['tank_id'])),
                  ('date_last_reading', '>=', start_date), ('date_last_reading', '<=', end_date)]
        tank_readings = request.env['tank.reading'].search(domain)
        average_usage = 0
        note = []
        dates = []
        for reading in tank_readings:
            x = x_date.index(reading.date_last_reading.strftime("%Y-%m-%d"))
            usage[x] += reading.usage
            average_usage += reading.usage
            dates.append(reading.date_last_reading.strftime("%Y-%m-%d"))              #This is used later to build DataTabe
            note.append(reading.narrative)          #This is used later to build DataTabe
        average_usage = round(average_usage/no_days,2)    # get daily average
        ave_label = "Daily Ave " + str(average_usage)

        """ ****************  start defining plot ******************    """

        header = "MANDLACHEM SOUTH AFRICA\n"
        header += "Usage Analysis Report\n"
        header += "From {} To {}\n".format(start_date, end_date)
        header += "Site: {}\n".format(site.name)
        header += "Line: {}\n".format(line.name)
        header += "Tank: {}".format(tank.name)


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
        chart_width = 1100
        chart_height = 550
        aspect_ratio = chart_width / chart_height
        path = "https://static.wixstatic.com/media/8eca0d_49d47e53e4a848b6b38c1028d7dfef18~mv2.png/v1/fill/w_446,h_196,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/MCSA%20Trans.png"
        #p = figure(title=header,  y_axis_label="Volume",
        p = figure(title=header,  y_axis_label="Volume",
                   toolbar_location="above",
                   width=chart_width,
                   height=chart_height,
                   )
        p.title.text_font = 'Raleway'
        p.toolbar.logo = None
        p.add_tools(HoverTool(tooltips=tooltips))
        # image = ImageURL(url=[path], x=len(usage)  , y=(y_max - y_min)*aspect_ratio*.1, w=5.8, h=(y_max - y_min)*aspect_ratio*.1)  # Position the logo
        # p.add_glyph(image)
        p.ray(x=[0], y=y_max, length=0, color="red", angle=0, line_width=3, line_dash="dotdash",legend_label=max_label)
        p.ray(x=[0], y=y_min, length=0, color="green", angle=0, line_width=3, line_dash="dashed",legend_label=min_label)
        p.ray(x=[0], y=average_usage, length=0, color="orange", angle=0, line_width=3, line_dash="dashdot",legend_label=ave_label)
        p.xaxis.major_label_overrides = {
            i: date for i, date in enumerate(x_date)
        }
        p.xaxis[0].ticker = FixedTicker(ticks=my_tickers)
        p.yaxis.formatter = NumeralTickFormatter(format="00")
        p.xaxis.major_label_orientation = 3.4142 / 4    # """ This orientates the date on its side """
        p.vbar( x=my_tickers, top=usage, width=0.5, legend_label="Usage", color='blue')
        p.legend.label_text_font = "Raleway"
        #p.legend.location = "top_left"

        """ Set up data for DataTable"""
        data = dict(
            dates=dates,
            notes=note,
        )
        source = ColumnDataSource(data)
        columns = [
            TableColumn(field="dates", title="Date",),
            TableColumn(field="notes", title="Notes", ),
        ]
        data_table = DataTable(source=source, columns=columns,autosize_mode="fit_columns", width=1200)

        string = file_html(Column(Row(p), Row(data_table)), CDN, "Tank Usage Report")
        return string


