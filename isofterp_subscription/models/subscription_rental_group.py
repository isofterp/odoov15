#!/usr/bin/env python
from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

class SubscriptionRentalGroup(models.Model):
    _name = "subscription.rental.group"
    _description = 'Machine Rental Groups'

    name = fields.Char('Ceded Rental')
    group_type = fields.Char('Type')
    group_code = fields.Char('Code')
    billable = fields.Boolean("Billable")
