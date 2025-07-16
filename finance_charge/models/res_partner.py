# -*- coding: utf-8 -*-
# Copyright 2020-2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    finance_charges = fields.Boolean(string = 'Finance Charges', default=True)

