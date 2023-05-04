# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Warning on Overdue Invoices - Field Services",
    "version": "14.0.1.0.0",
    "category": "Sales/Sales",
    "license": "AGPL-3",
    "summary": "Show overdue warning on field service form view",
    "author": "I-Soft Solutions",
    "maintainers": ["i-soft"],
    "website": "http://isoft.co.za",
    "depends": ["sale", "account_invoice_overdue_warn", "industry_fsm"],
    "data": [
        "views/project_view.xml",
    ],
    "installable": True,
}
