# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'i-SoftERP SupaLift',
    'version': '1.0',
    'category': 'Field Service',
    'summary': 'i-SoftERP SupaLift',
    'description': """ This module links the <aintenance module and the Industry_fsm module - module mame to change


    """,
    'author': 'i-Soft Solutions (Pty) Ltd',
    'depends': ['purchase', 'sale_stock', 'branch', 'project_task_code','web_tour', 'bus'],
    'data': [

        'views/project_view.xml',
        'views/maintenance_views.xml',
        'views/partner_view.xml',
        'views/sale_view.xml',
        ##'views/account_bank_statement_view.xml',
        'views/hr_expense_view.xml',
        'views/account_move_views.xml',
        'views/project_task_template_views.xml',
        'views/analytic_account_views.xml',
        'views/purchase_views.xml',
        'views/stock_picking_view.xml',
        'views/hr_timesheet_view.xml',
        'views/equipment_job_template_views.xml',
        'views/job_type_views.xml',
        'wizard/project_task_create_timesheet_views.xml',
        'wizard/purchase_make_invoice_advance_views.xml',
        'wizard/combined_order_view.xml',
        'security/isofterp_supalift_security.xml',
        'security/ir.model.access.csv',
        'data/supalift_data.xml'

    ],
    'assets': {
        'web.assets_backend': [
            'isofterp_supalift/static/src/js/*.js',
        ],
        'web.assets_qweb': [
            'isofterp_supalift/static/src/xml/cart_menu.xml',
        ],

    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
