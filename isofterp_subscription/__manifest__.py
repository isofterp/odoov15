# Copyright 2004-2010 OpenERP SA


{
    'name': 'I-Soft Subscription Management - Recurring',
    'version': '11.0.4.0.0',
    'category': 'Subscription Management',
    'license': 'AGPL-3',
    'author': "I-Soft Solutions",
    'website': 'https://github.com/oca/contract',
    'depends': ['base','account','analytic','sale','sale_subscription','industry_fsm','portal','project','helpdesk','account_followup'],
    'data': [

        'views/sale_subscription_view.xml',
        'views/sale_subscription_line.xml',
        'views/sale_view.xml',
        'views/subscription_machine_charge_view.xml',
        'views/subscription_portal_templates.xml',
        'views/subscription_rental_group_view.xml',
        'views/subscription_rental_factor_view.xml',
        'views/product_view.xml',
        'views/project_view.xml',
        'views/stock_production_lot_views.xml',
        'views/meter_reading_import_view.xml',
        'views/meter_click_combined_view.xml',
        'views/res_partner_view.xml',
        'data/data.xml',
        'wizard/add_hoc_increase_views.xml',
        'wizard/meter_reading_request_views.xml',






        'security/ir.model.access.csv',

    ],
    'installable': True,
}
