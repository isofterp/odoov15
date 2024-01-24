from odoo import api, fields, models, _, osv
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
#from odoo import exceptions
from odoo.exceptions import ValidationError

import pandas as pd
import tempfile
import xlsxwriter
import base64


df = pd.DataFrame()

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    x_no_charge = fields.Boolean("Tick here if you want to create a No Charge Invoice", help="Tick if you want a No-Charge Sale")
    x_lot_id = fields.Many2one('stock.production.lot', 'Serial Number')
    x_partner_dlv_street = fields.Char(related='partner_shipping_id.street', string='Street')
    x_partner_dlv_street2 = fields.Char(related='partner_shipping_id.street2', string='')
    x_partner_dlv_email = fields.Char(related='partner_shipping_id.email', string='')
    x_partner_dlv_phone = fields.Char(related='partner_shipping_id.phone', string='')
    x_partner_dlv_mobile = fields.Char(related='partner_shipping_id.mobile', string='')
    x_product_name = fields.Char(related='x_lot_id.product_id.product_tmpl_id.name')
    x_copies_black = fields.Char(string='Meter Reading (B&W)')
    x_copies_color = fields.Char(string='Meter Reading (Color)')
    x_account_number = fields.Char(related='partner_id.x_account_number', string='Account Number', store=True)
    x_main_partner = fields.Many2one('res.partner', readonly=True, tracking=True,
                                 states={'draft': [('readonly', False)]},
                                 check_company=True,
                                 string='Main Partner', change_default=True, ondelete='restrict')

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    x_account_number = fields.Char(related='partner_id.x_account_number', string='Account Number', store=True)








    




