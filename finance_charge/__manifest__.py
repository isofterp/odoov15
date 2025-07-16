# -*- coding: utf-8 -*-
# Copyright 2020-2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

{
    'name': "Finance Charge",
    'summary': """This module implements the functionality to create finance charges for past due customer invoices.""",
    'version': '15.0.1.0.0',
    'category': 'Accounting',
    'website': "https://www.sodexis.com/",
    'author': "Sodexis",
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'depends': [
            'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/generate_finance_charge_view.xml',
        'views/account_move_views.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': ['images/main_screenshot.png'],
    'live_test_url': 'https://youtu.be/JyyORml2My0',
    'price': 99.99,
    'currency': 'USD',
}
