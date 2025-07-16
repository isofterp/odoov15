from odoo import models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def reconcile_invoice(self):
        view = self.env.ref('ld_reconcile_invoices_from_payment.view_multi_invoices')
        if self.payment_type == 'inbound' and self.partner_type == 'customer':
            self.env.context = dict(self.env.context)
            self.env.context.update({'default_move_type_id': 'out_invoice', 'default_partner_id': self.partner_id.id})
        if self.payment_type == 'outbound' and self.partner_type == 'supplier':
            self.env.context = dict(self.env.context)
            self.env.context.update({'default_move_type_id': 'in_invoice', 'default_partner_id': self.partner_id.id})
        if self.payment_type == 'inbound' and self.partner_type == 'supplier':
            self.env.context = dict(self.env.context)
            self.env.context.update({'default_move_type_id': 'in_refund', 'default_partner_id': self.partner_id.id})
        if self.payment_type == 'outbound' and self.partner_type == 'customer':
            self.env.context = dict(self.env.context)
            self.env.context.update({'default_move_type_id': 'out_refund', 'default_partner_id': self.partner_id.id})

        return {
            'name': 'Multi Invoice Payment',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'multi.invoice',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
        }
