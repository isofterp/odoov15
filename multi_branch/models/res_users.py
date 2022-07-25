# See LICENSE file for full copyright and licensing details.
"""Res Users Model."""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    """Res Users Model."""

    _inherit = "res.users"

    def _branches_count(self):
        return self.env["multi.branch"].sudo().search_count([])

    def _compute_branches_count(self):
        branches_count = self._branches_count()
        for user in self:
            user.branches_count = branches_count

    branch_id = fields.Many2one(
        "multi.branch",
        string="Branch",
        help="The branch this user is currently \
                                working for.",
    )

    branch_ids = fields.Many2many(
        "multi.branch",
        "multi_barnch_users_rel",
        "user_id",
        "branch_id",
        string="Branches",
    )
    branches_count = fields.Integer(
        compute="_compute_branches_count",
        string="Number of Branches",
        default=_branches_count,
    )

    @api.model
    def create(self, vals):
        """Overridden create method to update branch in partner."""
        user = super(ResUsers, self).create(vals)
        # if user and user.partner_id and user.branch_id:
        #     user.partner_id.write({"branch_id": user.branch_id.id or False})
        return user

    def write(self, vals):
        """Overridden write method to update branch in partner."""
        res = super(ResUsers, self).write(vals)
        # if vals and vals.get("branch_id", False):
        #     for user in self:
        #         # if user.partner_id and user.branch_id:
        #         #     user.partner_id.write({"branch_id": user.branch_id.id or False})
        self.clear_caches()
        return res

    @api.constrains("branch_id", "branch_ids")
    def _check_branch(self):
        if self.branch_id:
            if any(user.branch_id not in user.branch_ids for user in self):
                raise ValidationError(
                    _(
                        "The chosen branch is not in the"
                        " allowed branches for this user!!"
                    )
                )
