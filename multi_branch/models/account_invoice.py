# See LICENSE file for full copyright and licensing details.
"""Account Invoice (Move) Model."""

from odoo import fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    """Sale Advance Payment Inv."""

    _inherit = "sale.advance.payment.inv"

    def _create_invoice(self, order, so_line, amount):
        """Overridden method to update branch in invoice(move)."""
        invoice = super(SaleAdvancePaymentInv, self)._create_invoice(
            order, so_line, amount
        )
        if order and order.branch_id:
            invoice.write({"branch_id": order.branch_id.id})
            if invoice.invoice_line_ids:
                invoice.invoice_line_ids.write({"branch_id": order.branch_id.id})
        return invoice


class AccountInvoiceReport(models.Model):
    """Account Invoice Report."""

    _inherit = "account.invoice.report"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")

    def _select(self):
        return (
            super(AccountInvoiceReport, self)._select()
            + ", move.branch_id as branch_id"
        )

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ", move.branch_id"
