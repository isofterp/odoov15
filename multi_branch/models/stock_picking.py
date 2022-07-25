# See LICENSE file for full copyright and licensing details.
"""Stock Picking Model."""

from odoo import api, fields, models


class StockPicking(models.Model):
    """Inherit Stock Picking."""

    _inherit = "stock.picking"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")

    @api.model
    def create(self, vals):
        """Overridden method to update the operations lines."""
        picking = super(StockPicking, self).create(vals)
        if picking and picking.branch_id:
            if picking.move_ids_without_package:
                picking.move_ids_without_package.write(
                    {"branch_id": picking.branch_id and picking.branch_id.id or False}
                )
        return picking

    def write(self, vals):
        """Overridden method to update the operations lines."""
        res = super(StockPicking, self).write(vals)
        if vals.get("branch_id", False):
            for picking in self:
                if picking.branch_id and picking.move_ids_without_package:
                    picking.move_ids_without_package.write(
                        {
                            "branch_id": picking.branch_id
                            and picking.branch_id.id
                            or False
                        }
                    )
        return res


class StockMove(models.Model):
    """Inherit Stock Move."""

    _inherit = "stock.move"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")

    def _get_new_picking_values(self):
        """Method _get_new_picking_values.

        Method is overridden from stock.move
        to set the branch in stock.picking.
        """
        result = super(StockMove, self)._get_new_picking_values()
        result.update(
            {
                "branch_id": self.sale_line_id
                and self.sale_line_id.order_id
                and self.sale_line_id.order_id.branch_id
                and self.sale_line_id.order_id.branch_id.id
                or False
            }
        )
        return result


class StockPickingType(models.Model):
    """Inherit Stock Picking Type."""

    _inherit = "stock.picking.type"

    branch_id = fields.Many2one(related="warehouse_id.branch_id", string="Branch Name")


class StockRule(models.Model):
    """Inherit Stock Rule."""

    _inherit = "stock.rule"

    def _get_stock_move_values(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        company_id,
        values,
    ):
        result = super(StockRule, self)._get_stock_move_values(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
        )
        if values:
            warehouse_id = values.get("warehouse_id", False)
            result.update(
                {
                    "branch_id": warehouse_id
                    and warehouse_id.lot_stock_id
                    and warehouse_id.lot_stock_id.branch_id
                    and warehouse_id.lot_stock_id.branch_id.id
                    or False
                }
            )
        return result

    def _prepare_purchase_order(self, company_id, origins, values):
        # Overridden to update the branch in RFQ generated while
        # placing the sale order when product is out of stock.
        result = super(StockRule, self)._prepare_purchase_order(
            company_id, origins, values
        )
        # values : As per the base module flow it will always in list of dict.
        # We did below code based method parameter changes in v13.0
        # ex: Module: purchase_requisition_stock, stock.py
        val = values and values[0] or {}
        if val and val.get("warehouse_id", False) and val.get("warehouse_id").branch_id:
            result.update({"branch_id": val.get("warehouse_id").branch_id.id or False})
        return result


class StockScrap(models.Model):
    """Inherited Stock Scrap model."""

    _inherit = "stock.scrap"

    def _prepare_move_values(self):
        res = super(StockScrap, self)._prepare_move_values()
        res.update(
            {
                "branch_id": self.location_id
                and self.location_id.branch_id
                and self.location_id.branch_id.id
                or False
            }
        )
        return res
