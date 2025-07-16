# License OPL-1 (See LICENSE file for full copyright and licensing details).

==============================
Account Invoice Finance Charge
==============================

Configuration
=============

To configure this module, you need to:

	1. In Accounting settings, navigate to “Finance Charge Configuration”

	2. Set the Finance Charge Product (service item to use on the invoice line)

	3. Set the Monthly Finance Charge Percentage (The percentage of overdue invoices that you will charge as a finance charge, on a monthly basis)

	4. Set the Finance Charge Payment Terms (The default terms that will be used on the invoice)

Usage
=====

To use this module, you need to:

	1. Set the “Finance Charges” boolean on the contact (Sales & Purchase tab). This defines that a contact will be considered for finance charges

		a. Note this is selected by default for new contacts

	2. Finance Charges can be generated in multiple ways

		a. From a contact

			=> Click the action dropdown, “Create Finance Charges”

		b. From an invoice

			=> Click the action dropdown, “Create Finance Charges”

		c. For all contacts at once

			=> Accounting > Customers > “Create Finance Charges”

		d. For a specific list of contacts

			=> In list view of contacts, select the checkbox for all the contacts you want, then use the action dropdown, “Create Finance Charges”

		e. For a specific list of invoices

			=> In list view of invoices, select the checkbox for all the invoices you want, then use the action dropdown, “Create Finance Charges”

	3. Once selecting “Create Finance Charges”, you are given a window to select a date

		a. “Due Date Prior To”, ex. 09/01 to run charges for August

		b. Any invoices with a due date prior to the date you select, will be considered for finance charges

	4. If finance charges are calculated, a new draft invoice will be created for each customer

	5. The reference field will list the invoices that were used to calculate the total amount. It will also list the month that it’s for. For example, if you select a “Due Date Prior To” of 09/01, it will say August


Credits
========

Contributors
------------
* Sodexis <apps@sodexis.com>

This module is maintained by Sodexis.
