#!/usr/bin/env python

#!/usr/bin/env python
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class SubscriptionChargesType(models.Model):
    _name = 'subscription.charges.type'
    _description = "Subscription charge types "

    name = fields.Char("Type")
    billable =  fields.Boolean('Billable')




