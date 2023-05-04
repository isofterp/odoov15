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












    




