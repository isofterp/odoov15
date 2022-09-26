#!/usr/bin/env python

#!/usr/bin/env python
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class SubscriptionRentalFactor(models.Model):
    _name = 'subscription.rental.factor'
    _description = "Subscription rental factor"

    name = fields.Char("Name")
    rate =  fields.Float('Rate', digits=(16,5))
    months = fields.Integer('Months')
    escalation = fields.Float('Escalation %')




