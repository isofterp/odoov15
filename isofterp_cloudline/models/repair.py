# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from random import randint

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

class Repair(models.Model):
    _inherit = "repair.order"

    @api.onchange('lot_id')
    def onchange_lot(self):
        if self.lot_id:
            self.partner_id = self.lot_id.x_partner_id
