# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo.tools.translate import _
from odoo import api, fields, models, _
from odoo.exceptions import Warning,UserError



class SupplierInvoiceLine(models.Model):
    _inherit = 'account.move.line'


