# -*- coding: utf-8 -*-
{
    'name': "User Permissions",

    'summary': " Edgar",

    'description': """
        Testing User permissions
    """,

    'author': "I-Soft Solutions",
    'website': "https://www.isoft.co.za",

    'category': 'Sales/Sales',
    'version': '1.0',

    'depends': ['base', 'sale','account'],
  

    'data': [
        'views/perms_views.xml',
        'security/ir.model.access.csv',
        'security/perms_security.xml',
    ],

    'application': True,
}
