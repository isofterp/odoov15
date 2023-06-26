# -*- coding: utf-8 -*-
{
    'name': "Geo, locate, draw into map case Partners Addon",

    'summary': "Sol map test res partner. ",
    'description': """
        Sol map test for res partner
    """,
    "category": "Web",
    'author': "0Solver0",
    'license': 'LGPL-3',
    'version': '15.0',
    'website': 'https://addons4.odoo.com/',
    'depends': ['sol_ol_map_draw','contacts','base_geolocalize'],
    'data': [
         "views/data.xml"
    ],
    'images': ['static/description/thumbnails_screenshot.png','static/description/icon.png'],
    'installable': True,
    'auto_install': False
}
