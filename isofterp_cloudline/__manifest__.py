# -*- coding: utf-8 -*-
{
    'name': "Isoft Cloudline",

    'summary': " Cloudline",

    'description': """
        Various Odoo customizations Cloudline
    """,

    'author': "I-Soft Solutions",
    'website': "https://www.isoft.co.za",

    'category': 'Sales/Sales',
    'version': '1.0',

    'depends': ['base', 'sale','account','repair','purchase'],
  

    'data': [
        # 'security/ir.model.access.csv',
        'views/purchase_views.xml',
        'views/stock_production_lot.xml',
        'views/product_views.xml',
        'views/mrp_bom_views.xml'
    ],

    'application': True,
}
