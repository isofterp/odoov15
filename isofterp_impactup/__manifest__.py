# -*- coding: utf-8 -*-
{
    'name': "Isoft Impact Up",

    'summary': " Isoft Impact Up",

    'description': """
        Various Odoo customizations  Impact Up
    """,

    'author': "I-Soft Solutions",
    'website': "https://www.isoft.co.za",

    'category': 'Sales/Sales',
    'version': '1.0',

    'depends': ['base', 'contacts', 'event','survey'],
  

    'data': [
        'views/res_partner_view.xml',

    ],

    'application': True,
}
