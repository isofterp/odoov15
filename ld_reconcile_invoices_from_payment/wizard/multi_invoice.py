import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MultiInvoice(models.TransientModel):
    _name = 'multi.invoice'
    _description = 'Multi Invoice'

    invoice_ids = fields.Many2many('account.move', 'multi_invoice_and_move_line_rel', required=True, string='Invoice')
    total = fields.Float(string="Invoice Total")
    partner_id = fields.Many2one('res.partner', )
    move_type_id = fields.Selection([
        ('entry', 'Journal Entry'),
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Credit Note'),
        ('in_invoice', 'Vendor Bill'),
        ('in_refund', 'Vendor Credit Note'),
        ('out_receipt', 'Sales Receipt'),
        ('in_receipt', 'Purchase Receipt'),
    ], string='Type')

    @api.onchange("invoice_ids")
    def _get_invoice_total(self):
        total = 0
        for invoice in self.invoice_ids:
            total = total + invoice.amount_total
        self.total = total

    def confirm_invoices(self):
        pay_obj = self.env['account.payment'].browse(self.env.context.get('active_id'))
        if not pay_obj.amount >= self.total:
            raise UserError("Please select Invoices that have total less then {}.".format(pay_obj.amount))
        for rec in self.invoice_ids:
            move_lines = pay_obj.line_ids.filtered(lambda record: record.account_internal_type in ('receivable', 'payable') and not record.reconciled)
            for line in move_lines:
                rec.js_assign_outstanding_line(line.id)
