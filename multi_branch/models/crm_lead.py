# See LICENSE file for full copyright and licensing details.
"""CRM Lead Model."""


from odoo import fields, models


class Lead(models.Model):
    """CRM Lead Model."""

    _inherit = "crm.lead"

    branch_id = fields.Many2one(
        "multi.branch",
        string="Branch Name",
        default=lambda self: self.env.user.branch_id,
        ondelete="restrict",
    )
