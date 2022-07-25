# See LICENSE file for full copyright and licensing details.

{
    # Module information
    "name": "Multi Branch",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "category": "Extra Tools",
    "sequence": "1",
    "summary": """Multiple Branch Management for single company,
    Assign One Or Multiple Branch to user,
    Branch Management.""",
    # Author
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "website": "http://www.serpentcs.com",
    # Dependencies
    "depends": ['base',],
    # Views
    "data": [
        "security/multi_branch_security.xml",
        "security/ir.model.access.csv",
       # "wizard/wiz_branch_warehouse_view.xml",
        # "report/sale_report_templates.xml",
        # "report/purchase_order_templates.xml",
        # "report/report_invoice.xml",
        # "report/report_stockpicking_operations.xml",
        # "report/report_payment_receipt_templates.xml",
        "views/multi_branch_view.xml",
        "views/res_users_view.xml",
        # "views/sale_order_view.xml",
        # "views/stock_warehouse_view.xml",
        # "views/account_invoice_view.xml",
        # "views/stock_picking_view.xml",
        # "views/account_payment.xml",
        # "views/purchase_order_view.xml",
        # "views/stock_location_view.xml",
        # "views/account_bank_statement_view.xml",
    ],
    # Odoo App Store Specific
    "images": ["static/description/odoo-app-banner-multi-branch.jpg"],
    "live_test_url": "https://www.youtube.com/watch?v=mnbG1Lo0NGA",
    # Technical
    "installable": True,
    # "post_init_hook": "_disable_security_rules",
    # "uninstall_hook": "_enable_security_rules",
    "application": True,
    "auto_install": False,
    "price": 79,
    "currency": "EUR",
}
