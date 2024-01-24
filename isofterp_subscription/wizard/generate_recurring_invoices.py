# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

class GenerateRecurringInvoices(models.TransientModel):
    _name = 'generate.recurring.invoices.wizard'
    _description = 'Generate Recurring Invoices'

    current_user = fields.Char('Current User',default=lambda self: self.env.user.name)
    yes_to_backup = fields.Char("Have you made a Backup of the Database? If so, enter 'Yes' in this field.")


    def generate_recurring_invoices(self):
        if self.yes_to_backup != 'Yes':
            raise ValidationError(
                _('You did not enter a correct answer'))
        logging.warning("Running invoices")
        execute_cron = self.env['sale.subscription'].generate_recurring_invoice()

        return True

