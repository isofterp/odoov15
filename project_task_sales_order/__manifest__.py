# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt. Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': "Create Sales Quote from Project Task.",
    'version': '2.2.1',
    'license': 'Other proprietary',
    'price': 29.0,
    'currency': 'EUR',
    'summary': """This app allows you to create a sales quotation / sales order from project task.""",
    'description': """
sales order from project task
sales order with project task

    """,
    'author': "Probuse Consulting Service Pvt. Ltd.",
    'website': "http://www.probuse.com",
    'support': 'contact@probuse.com',
    'images': ['static/description/img12.jpg'],
    'live_test_url': 'https://youtu.be/bhsO5IrZvwg',
    'category': 'Project/Project',
    'depends': [
        'sale',
        'project',
        'branch',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/task_so_createview.xml',
        'wizard/meter_reading.xml',
        'wizard/create_travel_wizard_view.xml',
        'views/task_views.xml',
        'views/sale_view.xml',

    ],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
