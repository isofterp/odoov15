# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Stock Picking/Move from Invoice/Refund in Odoo',
    'version': '14.0.0.6',
    'category': 'Warehouse',
    'summary': 'Stock Picking from Invoice stock move from invoice stock picking from Refund stock move from refund invoice from picking stock picking from bill stock move from bill stock picking from vendor bill stock move from vendor bill picking from customer invoice',
    'description': """
    This module helps to create a stock move and picking while validating a invoice.
    odoo Create Stock Picking from Invoice Create Stock Move from Invoice Create Stock Moves With Invoice And Refunds
    odoo inventory move With Invoice And Refunds Create Picking from Invoice 
    odoo invoice based stock move refund based stock move odoo Create Stock Picking and Stock Move from Invoice
    odoo Create Stock Picking from Invoice refund Create Stock Move from Invoice refund
    odoo Create Stock Picking from refund Create Stock Move from refund
    odoo Create Picking from Invoice Create Move from Invoice Create Picking from Invoice
    odoo Picking from Invoice from picking odoo Create Stock Picking Stock Move from Invoice Refund in odoo
    odoo Stock Picking odoo Stock Move from Invoice Stock Picking from Invoice Stock Move from Invoice
    odoo Picking from Customer Invoice Picking from Customer Invoice Invoice From Picking
    odoo vendor bills from Picking vendor bills from Picking Delivery Order Incoming Shipment
    odoo supplier invoices from Incoming Shipment supplier invoices from Delivery Order
    odoo vendor invoices from Incoming Shipment vendor invoices from Delivery Order
    odoo vendor bills from Incoming Shipment vendor bills from Delivery Order
    odoo invoices from Delivery Order invoices from Incoming Shipment
    odoo invoice from Shipment Stock Move from Invoice Stock Picking from Invoice and Vendor Bill
    odoo Stock Picking from Vendor Bill Picking from Vendor Bill Vendor Bill to Incoming Shipment
    odoo invoice from Shipment Account invoice from picking invoice from stock picking


    odoo Create Stock Picking from customer Invoice Create Stock Move from customer Invoice Create Stock Moves With customer Invoice And customer Refunds
    odoo inventory move With customer Invoice And Refunds Create Picking from customer Invoice 
    odoo customer invoice based stock move customer refund based stock move odoo Create Stock Picking and Stock Move from vendor bills
    odoo Create Stock Picking from customer Invoice refund Create Stock Move from Invoice supplier refund
    odoo Create Stock Picking from vendor refund Create Stock Move from refund customer refund vendor picking
    odoo Create Picking from customer Invoice Create Move from customer Invoice Create Picking from customer Invoice
    odoo Picking from supplier Invoice from picking odoo Create Stock Picking Stock Move from supplier Invoice Refund in odoo
    odoo Stock Picking odoo Stock Move from customer Invoice Stock Picking from supplier Invoice Stock Move from Invoice
    odoo Picking from supplier Invoice Picking from supplier Invoice Invoice From Picking
    odoo supplier bills from picking supplier bills from Picking Delivery Order Incoming Shipment
    odoo supplier invoices from Incoming Shipment supplier invoices from Delivery Order
    odoo vendor invoices from Incoming Shipment vendor invoices from Delivery Order
    odoo vendor bills from Incoming Shipment vendor bills from Delivery Order
    odoo invoices from Delivery Order invoices from Incoming Shipment
    odoo invoice from Shipment Stock Move from Invoice Stock Picking from Invoice and Vendor Bill
    odoo Stock Picking from Vendor Bill Picking from Vendor Bill Vendor Bill to Incoming Shipment
    odoo invoice from Shipment Account invoice from picking invoice from stock picking



     Création de stock picking à partir de la facture
     Créer un mouvement de stock à partir de la facture
     Créer une cueillette à partir d'une facture
     Création de stock picking et de stock à partir de la facture
     Création de stock picking à partir du remboursement de facture
     Créer un mouvement de stock à partir du remboursement de facture
     Créer un stock picking à partir du remboursement
     Créer Stock Move à partir du remboursement
     Créer une cueillette à partir d'une facture
     Créer un mouvement à partir de la facture

     Crear Stock Picking from Invoice
     Crear Stock Move from Invoice
     Crear Picking de Factura
     Crear Stock Picking y Stock Move from Invoice
     Crear Stock Picking from Invoice refund
     Crear Stock Move from Invoice refund
     Crear Stock Picking from refund
     Crear Stock Mover de reembolso
     Crear Picking de Factura
     Crear mover de la factura
""",
    'author': 'BrowseInfo',
    'price': 25,
    'currency': "EUR",
    'website': 'https://www.browseinfo.in',
    'depends': ['account','stock', 'purchase','sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_invoice_view.xml',
        'wizard/accountconfig.xml',
    ],
    'live_test_url':'https://youtu.be/G1wb9R_0LJI',
    'installable': True,
    'auto_install': False,
    'application': True,
    'images':['static/description/Banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
