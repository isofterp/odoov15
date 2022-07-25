# See LICENSE file for full copyright and licensing details.
"""Stock Location model."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class Location(models.Model):
    """Stock Location Inherited."""

    _inherit = "stock.location"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")

    @api.onchange("branch_id")
    def _onchange_branch_id(self):
        # onchange method to rise warning branch id same as warehouse
        # configuration.
        for location in self:
            loc_id = location.location_id and location.location_id.id or False
            warehouse = self.env["stock.warehouse"].search(
                [("view_location_id", "=", loc_id)], limit=1
            )
            if (
                warehouse
                and warehouse.branch_id
                and warehouse.branch_id != location.branch_id
            ):
                raise UserError(
                    _(
                        "You must select same branch on a location "
                        "as assigned on a warehouse configuration."
                    )
                )


class Inventory(models.Model):
    """Stock Inventory Inherited."""

    _inherit = "stock.inventory"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")


class InventoryLine(models.Model):
    """Stock Inventory Line Inherited."""

    _inherit = "stock.inventory.line"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")
