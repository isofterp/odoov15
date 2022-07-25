# See LICENSE file for full copyright and licensing details.
"""Account and Payment Related Models."""

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

class AccountPayment(models.Model):
    """Account Payment."""

    _inherit = "account.payment"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")

    @api.model
    def default_get(self, fields):
        """Overridden Method to update branch in Payment."""
        rec = super(AccountPayment, self).default_get(fields)
        active_ids = self._context.get("active_ids") or self._context.get("active_id")
        invoices = (
            self.env["account.move"]
            .browse(active_ids)
            .filtered(lambda move: move.is_invoice(include_receipts=True))
        )
        if invoices:
            rec["branch_id"] = (
                invoices[0].branch_id and invoices[0].branch_id.id or False
            )
        return rec

    def post(self):
        """Overridden Method to update branch in payment."""
        res = super(AccountPayment, self).post()
        for payment in self:
            if payment.invoice_ids and not payment.branch_id:
                for invoice in payment.invoice_ids:
                    payment.branch_id = (
                        invoice.branch_id and invoice.branch_id.id or False
                    )
                    break
        return res

    def _prepare_payment_moves(self):
        """Overridden Method to update branch in payment move lines."""
        self.ensure_one()
        all_move_vals = super(AccountPayment, self)._prepare_payment_moves()
        for move_val in all_move_vals:
            move_val.update(
                {"branch_id": self.branch_id and self.branch_id.id or False}
            )
            for line_val in move_val.get("line_ids", []):
                if line_val and len(line_val) >= 3:
                    line_val[2].update(
                        {"branch_id": self.branch_id and self.branch_id.id or False}
                    )
        return all_move_vals


class AccountMoveLine(models.Model):
    """Account Move Line."""

    _inherit = "account.move.line"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")

class AccountMove(models.Model):
    """Account Move."""

    _inherit = "account.move"

    branch_id = fields.Many2one(
        "multi.branch",
        string="Branch Name",
        default=lambda self: self.env.user.branch_id,
        ondelete="restrict",
    )

    # @api.model
    # def create(self, vals_list1):
    #
    #     if self._context.get('default_move_type') == 'in_invoice':
    #         #vals_list1 = self._move_autocomplete_invoice_lines_create(vals_list1)
    #         vals_list = vals_list1
    #         logging.warning("Vals type is %s", vals_list)
    #         logging.warning("The vals in create is %s", type(vals_list))
    #         # OVERRIDE
    #         if vals_list.get('state') == 'posted':
    #
    #             raise UserError(_(
    #                 'You cannot create a move already in the posted state. Please create a draft move and post it after.'))
    #
    #
    #
    #
    #         # Manually create the invoice as calling the super does not set the task_id or Branch details
    #         invoice_vals = []
    #         invoice_line_ids_new = []
    #
    #         #rslt = super(AccountMove, self).create(vals_list)
    #
    #         inv_vals = {
    #             'move_type': self._context.get('default_move_type'),
    #             'ref': vals_list1.get('ref') or False,
    #             'journal_id': vals_list1.get('journal.id'),
    #             'partner_id': vals_list1.get('partner_id'),
    #             'currency_id': vals_list1.get('currency_id'),
    #             'fiscal_position_id': vals_list1.get('fiscal_position_id') or False,
    #             'invoice_date': vals_list1.get('date'),
    #             'partner_shipping_id': vals_list1.get('partner_shipping_id'),
    #             'invoice_date_due': vals_list1.get('invoice_date_due'),
    #             'state': 'draft',
    #         }
    #
    #         # Bow get the invoice_line_ids from vals_list - There is a better loop method
    #         invoice_line_ids = vals_list1.get('line_ids')
    #         logging.warning("invoice_line_ids %s", invoice_line_ids)
    #
    #         for lines in invoice_line_ids:
    #             #logging.warning("The type here is %s %s", type(lines), lines)
    #             line_dict = lines[2]
    #             if line_dict.get('name') != 'Standard Rate' and line_dict.get('name') is not False:
    #                 logging.warning("The type in lines is %s %s", type(line_dict), line_dict)
    #                 inv_line = {
    #                     'name': line_dict.get('name'),
    #                     'product_id': line_dict.get('product_id'),
    #                     'product_uom_id': line_dict.get('product_uom_id'),
    #                     'quantity': line_dict.get('quantity'),
    #                     'account_id': line_dict.get('account_id'),
    #                     'display_type': line_dict.get('display_type'),
    #                     'tax_ids': line_dict.get('tax_ids'),
    #                     'parent_state':line_dict.get('parent_state'),
    #                     'price_unit': line_dict.get('price_unit'),
    #                     'branch_id': line_dict.get('branch_id'),
    #                     'x_task_id': line_dict.get('x_task_id'),
    #                 }
    #                 invoice_tuple = (0, 0, inv_line)
    #                 invoice_line_ids_new.append(invoice_tuple)
    #
    #         inv_vals['line_ids'] = invoice_line_ids_new
    #         logging.warning("Creating move recordsinv vals is %s", inv_vals)
    #         # raise UserError(_(
    #         #     'You cannot create a move already in the posted state. Please create a draft move and post it after.'))
    #
    #         moves = self.env['account.move'].create(inv_vals)
    #         # for i, vals in enumerate(vals_list):
    #         #     if 'line_ids' in vals:
    #         #         moves[i].update_lines_tax_exigibility()
    #         return moves
    #     else:
    #         moves = super(AccountMove, self).create(vals_list1)
    #         return moves

    @api.model
    def create(self, vals):
        """Overridden create method to update the lines."""
        new_move = super(AccountMove, self).create(vals)
        #print('VALS=  ',vals)
        # The below code sets all the move lines with the same branch
        # This has the issue in that everything on the vendor bill will be for the same branch which is not
        # necessarily wrong
        # The same however cannot be saud for the job number. Each line will have to have its own job number set

        if new_move and new_move.branch_id:
            print("in multi branch - standard @ around line 98")
            if new_move.line_ids:
                new_move.line_ids.write(
                    {"branch_id": new_move.branch_id and new_move.branch_id.id or False,}
                )

                # Get the invoice line ids from vals
                tmp_lines_list = vals.get('invoice_line_ids')
                #logging.warning("Lines in list is %s", tmp_lines_list[0])
            if new_move.line_ids and new_move.move_type in ['out_invoice', 'out_refund', 'out_receipt']:
                new_move.line_ids.write(
                    {"x_task_id": new_move.x_task_id and new_move.x_task_id.id or False, }
                )

            if new_move.invoice_line_ids:
                new_move.invoice_line_ids.write(
                    {"branch_id": new_move.branch_id and new_move.branch_id.id or False,
                     }
                )

                logging.warning("Line - 179 The vals in create is %s", vals)
                tmp_lines_list = vals.get('invoice_line_ids')
                logging.warning("Lines in list is %s", tmp_lines_list)
                if tmp_lines_list:
                    for tmp_lines in tmp_lines_list:
                        for tmp_line in tmp_lines:
                            if isinstance(tmp_line,dict):
                                logging.warning("The dict is %s", tmp_line)
                                # Find the move line rec in the new record that matches this line
                                inv_line = self.env['account.move.line'].search([('move_id','=',new_move.id),
                                                                             ('product_id','=', tmp_line.get('product_id')),
                                                                              ('quantity','=', tmp_line.get('quantity')),])
                                if inv_line:
                                    #logging.warning("Found line with ID %s", inv_line.id)
                                    inv_line.write({'x_task_id': tmp_line.get('x_task_id'),
                                                    'x_project_id': tmp_line.get('x_project_id')})
                else:
                    logging.warning("For some reason we didnt get any tmp_lines_list")
            if new_move.invoice_line_ids and new_move.move_type in ['out_invoice', 'out_refund', 'out_receipt']:
                new_move.invoice_line_ids.write(
                    {"x_task_id": new_move.x_task_id and new_move.x_task_id.id or False,
                     }
                )
        return new_move

    def write(self, vals):
        """Overridden write method to update the lines."""
        #print('In the write statement of Account Move %s', vals)
        res = super(AccountMove, self).write(vals)
        if vals.get("branch_id", False):
            for inv in self:
                print("INV in self is %s", inv)
                if inv and inv.branch_id:
                    if inv.line_ids:
                        inv.line_ids.write(
                            {"branch_id": inv.branch_id and inv.branch_id.id or False,}
                        )
                    if inv.invoice_line_ids:
                        inv.invoice_line_ids.write(
                            {"branch_id": inv.branch_id and inv.branch_id.id or False,}
                        )
        if vals.get("x_task_id", False):
            for inv in self:
                print("INV in self is %s", inv)
                if inv and inv.x_task_id:
                    if inv.line_ids:
                        inv.line_ids.write(
                            {"x_task_id": inv.x_task_id and inv.x_task_id.id or False, }
                        )
                    if inv.invoice_line_ids:
                        inv.invoice_line_ids.write(
                            {"x_task_id": inv.x_task_id and inv.x_task_id.id or False, }
                        )
        return res

