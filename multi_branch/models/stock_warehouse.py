# See LICENSE file for full copyright and licensing details.
"""Stock Warehouse Model."""

from odoo import api, fields, models


class StockWarehouse(models.Model):
    """Stock Warehouse Model."""

    _inherit = "stock.warehouse"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")

    @api.model
    def create(self, vals):
        """Overridden create to update the branch in location."""
        warehouse = super(StockWarehouse, self).create(vals)
        if (
            warehouse
            and warehouse.branch_id
            and warehouse.view_location_id
            and not warehouse.view_location_id.branch_id
        ):
            warehouse.view_location_id.write(
                {"branch_id": warehouse.branch_id.id or False}
            )
        return warehouse

    def _get_locations_values(self, vals, code=False):
        """Overridden method to update the branch."""
        code = vals.get("code", False) or self.code
        result = super(StockWarehouse, self)._get_locations_values(vals, code)
        if vals.get("branch_id", False):
            for location in result.keys():
                result[location].update({"branch_id": vals["branch_id"]})
        return result

    @api.onchange("branch_id")
    def _onchange_branch_id(self):
        # Onchange method to update branch in location and Operation Types.
        for warehouse in self:
            vals = {
                "branch_id": warehouse.branch_id and warehouse.branch_id.id or False
            }
            if warehouse.view_location_id:
                warehouse.view_location_id.write(vals)
            if warehouse.wh_input_stock_loc_id:
                warehouse.wh_input_stock_loc_id.write(vals)
            if warehouse.wh_qc_stock_loc_id:
                warehouse.wh_qc_stock_loc_id.write(vals)
            if warehouse.wh_output_stock_loc_id:
                warehouse.wh_output_stock_loc_id.write(vals)
            if warehouse.wh_pack_stock_loc_id:
                warehouse.wh_pack_stock_loc_id.write(vals)

            if warehouse.pick_type_id:
                warehouse.pick_type_id.write(vals)
            if warehouse.pack_type_id:
                warehouse.pack_type_id.write(vals)
            if warehouse.out_type_id:
                warehouse.out_type_id.write(vals)
            if warehouse.in_type_id:
                warehouse.in_type_id.write(vals)
            if warehouse.int_type_id:
                warehouse.int_type_id.write(vals)
