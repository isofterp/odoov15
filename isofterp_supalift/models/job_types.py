# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date

from datetime import date, timedelta
from itertools import groupby
from stdnum.iso7064 import mod_97_10
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import json
import re
import logging
import psycopg2

_logger = logging.getLogger(__name__)

class JobTypes(models.Model):
    _name = "job.card.types"
    _description = " Job Card Types"

    name = fields.Char('Job Type', required=True)