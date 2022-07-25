# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import date
from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    site_id = fields.Many2one('site.site',string='Site')

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    site_id = fields.Many2one('site.site', string='Site')

  