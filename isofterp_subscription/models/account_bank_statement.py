from odoo import api, fields, models, _, osv
import logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
#from odoo import exceptions
from odoo.exceptions import ValidationError

import pandas as pd
import tempfile
import xlsxwriter
import base64
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class AccountBankStatement(models.Model):

    _inherit = "account.bank.statement"

    @api.depends('line_ids', 'balance_start', 'line_ids.amount', 'balance_end_real')
    def _end_balance(self):
        for statement in self:
            statement.total_entry_encoding = sum([line.amount for line in statement.line_ids])
            statement.balance_end = statement.balance_start + statement.total_entry_encoding
            statement.difference = statement.balance_end_real - statement.balance_end
            statement.balance_end_real = statement.balance_end





    




