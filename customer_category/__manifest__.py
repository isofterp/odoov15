# -*- coding: utf-8 -*-
{
    'name': "Customer Category",

    'summary': """Customer Classification""",
    'images': ['static/img/gkist-eg.jpeg'],
    'description': """
        Add customer classification in sales order to track 
        partner category sales
        customer code based on category
            """,
    'author': "GK for integrated smart technologies",
    'website': "http://www.gkist-eg.com",
    'category': 'Sales/Sales',
    'version': '0.1',
    'depends': ['sale','project','isofterp_subscription','industry_fsm'],
    'license': 'LGPL-3',
    'data': [
         'security/ir.model.access.csv',
         'views/views.xml',
         'views/templates.xml',
    ],
    'demo': [],
}
