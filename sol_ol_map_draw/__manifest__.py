# -*- coding: utf-8 -*-
{
    'name': "base module for Geo, Locate and Draw into map for odoo addons",

    'summary': "base module for showing entities in open street map, draw and geocoding",
    'description': """
        base module for showing entities in open street map, draw and geocoding,
    """,
    "category": "Web",
    'author': "0Solver0",
    'version': '15.0',
    'website': 'https://addons4.odoo.com/',
    'license': 'LGPL-3',
    # 'price': '0',
    # 'currency': '0',
    'depends': ['web'],
    'data': [
         #"views/assets.xml",
         "views/data.xml",
         "data/data_data.xml",
         'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'sol_ol_map_draw/static/src/js/solmap_common.js',
            'sol_ol_map_draw/static/src/js/main_view.js',
            'sol_ol_map_draw/static/src/js/map_form.js',
            'sol_ol_map_draw/static/src/scss/main_view.scss',
            'sol_ol_map_draw/static/src/scss/map_form.scss',
            ],
        'web.assets_qweb': [
            'sol_ol_map_draw/static/src/xml/solmaptemplate.xml',
            'sol_ol_map_draw/static/src/xml/solmapform.xml',
            ],
        },
    'images': ['static/description/thumbnails_screenshot.png','static/description/icon.png'],
    'qweb': ['static/src/xml/solmaptemplate.xml','static/src/xml/solmapform.xml'],
    'installable': True,
    'uninstall_hook': 'uninstall_hook',
    'auto_install': False
}
