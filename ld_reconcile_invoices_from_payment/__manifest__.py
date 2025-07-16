# -*- coding: utf-8 -*-
{
    'name': 'Multi Invoice Payment For Customer and Vendor',
    'version': '14.0',
    'category': 'Sales',
    'summary': 'User can do payment of multiple invoice at same time of same customer.',

    'depends': ['sale_management', 'account', ],
    "license": "LGPL-3",

    'data': [
        'security/ir.model.access.csv',
        'views/account_payment.xml',
        'wizard/multi_invoice.xml',
    ],

    'author': "Livedigital Technologies Private Limited",
    'website': "ldtech.in",
    'support': 'suresh.hiyal@ldtech.in',
    'maintainer': 'Livedigital Technologies Private Limited',
    'images': ['static/description/icon.png'],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url': 'https://www.youtube.com/watch?v=MXCiB0ETie4&t=18s'
}
