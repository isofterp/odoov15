# See LICENSE file for full copyright and licensing details.
"""Purchase model."""

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    """Purchase Order."""

    _inherit = "purchase.order"

    branch_id = fields.Many2one(
        "multi.branch",
        string="Branch Name",
        default=lambda self: self.env.user.branch_id,
        ondelete="restrict",
    )

    @api.model
    def default_get(self, fields):
        """Overridden default get to set warehouse picking."""
        result = super(PurchaseOrder, self).default_get(fields)
        type_obj = self.env["stock.picking.type"]
        company_id = self.env.company.id or False
        branch_id = self.env.user.branch_id.id or False
        types = type_obj.search(
            [
                ("code", "=", "incoming"),
                ("warehouse_id.company_id", "=", company_id),
                ("branch_id", "=", branch_id),
            ],
            limit=1,
        )
        result.update({"picking_type_id": types and types.id or False})
        return result

    @api.onchange("branch_id", "company_id")
    def _onchange_branch_id(self):
        """Onchange method to update the picking type in purchase order."""
        type_obj = self.env["stock.picking.type"]
        company_id = (
             self.env.company.id or False
        )
        for purchase in self:
            branch_id = purchase.branch_id and purchase.branch_id.id or False
            company_id = purchase.company_id and purchase.company_id.id or company_id
            types = type_obj.search(
                [
                    ("code", "=", "incoming"),
                    ("warehouse_id.company_id", "=", company_id),
                    ("branch_id", "=", branch_id),
                ],
                limit=1,
            )
            purchase.picking_type_id = types and types.id or False

    @api.model
    def _prepare_picking(self):
        result = super(PurchaseOrder, self)._prepare_picking()
        result.update({"branch_id": self.branch_id and self.branch_id.id})
        return result

    def action_view_invoice(self, invoices=False):
        """Method Action view invoice."""
        if invoices:
            invoices.write({"branch_id": self.branch_id and self.branch_id.id or False})
        return super(PurchaseOrder, self).action_view_invoice(invoices)


class PurchaseOrderLine(models.Model):
    """Purchase Order Line."""

    _inherit = "purchase.order.line"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")

    def _prepare_stock_moves(self, picking):
        result = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        if picking:
            for pick in result:
                pick.update(
                    {"branch_id": picking.branch_id and picking.branch_id.id or False}
                )
        return result


class PurchaseReport(models.Model):
    """Purchase Report."""

    _inherit = "purchase.report"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")

    def _select(self):
        return super(PurchaseReport, self)._select() + ", po.branch_id as branch_id"

    def _group_by(self):
        return super(PurchaseReport, self)._group_by() + ", po.branch_id"
