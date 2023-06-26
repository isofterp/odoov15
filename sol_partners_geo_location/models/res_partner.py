# -*- coding: utf-8 -*-
#################################################################################
#
#
#################################################################################

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"
    map_form = fields.Char(string="map form",store=True)