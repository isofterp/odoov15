# See LICENSE file for full copyright and licensing details.
"""Res Partner Model."""

from odoo import fields, models


class ResPartner(models.Model):
    """Res Partner Model."""

    _inherit = "res.partner"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")
