# -*- coding: utf-8 -*-
{
    'name': "Isoft MandlaChem",

    'summary': " MandlaChem",

    'description': """
        Various Odoo customizations MandlaChem
    """,

    'author': "I-Soft Solutions",
    'website': "https://www.isoft.co.za",

    'category': 'Sales/Sales',
    'version': '1.0',

    'depends': ['base', 'sale', 'account', 'mrp', 'stock'],
  

    'data': [
        'security/ir.model.access.csv',
        #'security/multi_branch_security.xml',

        'views/site_views.xml',
        'views/tank_views.xml',
        'views/mrp_production_views.xml',
        #'views/res_users_view.xml',
        'wizard/tank_reading_report_view_wiz.xml',
        # this is the latest

        'report/tank_usage_report.xml',
        'report.xml',

    ],

    'application': True,
}
