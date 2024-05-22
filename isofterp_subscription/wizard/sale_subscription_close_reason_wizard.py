# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging


class SaleSubscriptionCloseReasonWizard(models.TransientModel):
    _inherit = "sale.subscription.close.reason.wizard"

    close_reason_id = fields.Many2one("sale.subscription.close.reason", string="Close Reason")
    x_is_donate = fields.Boolean(string="Is machine donated")

    def lookup_stock_move(self,main_machine,subscription ):
        logging.warning('Looking up stock moves')
        stock_move = self.env['stock.move'].search([('product_id', '=', main_machine.product_id.id),
                                                    ('partner_id', '=', subscription.partner_id.id),
                                                    ('picking_type_id.code', '=', 'incoming'),
                                                    ('move_line_ids.lot_name', '=', main_machine.name)])
        return stock_move
    def create_inverse_analytic_line(self,main_machine):
        #logging.warning('Create inverse analytic line')
        analytic_acc = self.env['account.analytic.account'].search([('name', '=', main_machine.name)])
        if analytic_acc:
            analytic_acc_lines = self.env['account.analytic.line'].search([('account_id', '=', analytic_acc.id)])
            if analytic_acc_lines:
                total_amount = 0
                contra_amount = 0
                for acc_line in analytic_acc_lines:
                    # Add up all the amounts
                    total_amount += acc_line.amount
                #logging.warning("The total is %s", total_amount)
                # Create an entry to zerorize the account
                if total_amount < 0 or total_amount > 0:
                    contra_amount = total_amount * -1
                    #logging.warning("The contra amount is %s", contra_amount)
                    new_acc_line = self.env['account.analytic.line'].create({
                        'name': 'Contract Termination',
                        'account_id': analytic_acc.id,
                        'amount': contra_amount
                    })
                    if new_acc_line:
                        logging.warning("New line created")
                    else:
                        logging.warning("Failed to create new anal line")
            else:
                raise UserError(_("COULD NOT FIND ANALYTIC LINES"))
        else:
            raise UserError(_("COULD NOT FIND ANALYTIC ACCOUNT"))

    def unset_values_on_lot(self, main_machine):
        logging.warning('Unset Values on lot')
        main_machine.x_subscription_id = None
        main_machine.x_dlv_id = None
        logging.warning('Unset Values on lot -  Done')

    def unlink_machine_on_contract(self, subscription):
        logging.warning("Unlinking machine ids from contract")
        for machine in subscription.x_machine_ids:
            message = 'Contract :' + subscription.name + '\n Terminated ' + '\n Partner: ' + subscription.partner_id.name + '\n Serial No: ' + \
                      machine.name + '\n Reason: ' + self.close_reason_id.name
            subscription.sudo().message_post(body=message)
        subscription.x_machine_ids = None

    def set_close(self):

        # Before calling super do the following
        # 1. Check if the main product on the contract is in an internal warehouse location
        # (a) Don't think we need to go through delivery orders but let see
        # If 1 is satisfied, we can now do some maintenance work
        # 2. Go to the analytic account of the machine
        # (a) - Check what the last entry or balance is and post a contra entry
        # (b) - Add a note onto the analytic account to indicate that the contract is closed
        # (c) - Might need to remove the contract details from the analytic account
        # 3. Go to the serial number/lot and remove the contract details and delivery address
        # (a) Add a note to this effect
        # 4. Remove the main machine from the existing contract
        # (a) Add a note to this effect

        self.ensure_one()
        subscription = self.env['sale.subscription'].browse(self.env.context.get('active_id'))
        machines = subscription.x_machine_ids

        logging.warning("Machines are %s on sub %s", machines, subscription.name)
        main_machine = self.env['stock.production.lot'].search([('x_subscription_id', '=', subscription.id),
                                                                ('x_main_product', '=', True)])
        message = 'Contract :' + subscription.name + ' Terminated ' + ' Partner: ' + subscription.partner_id.name + ' Serial No: ' + \
                  main_machine.name + ' Reason: ' + self.close_reason_id.name
        logging.warning("The contact and main product is %s %s", main_machine.name, main_machine.delivery_ids)

        # Search stock move or stock picking records for this machine.
        if not self.x_is_donate:
            stock_move = self.lookup_stock_move(main_machine,subscription)
            if not stock_move:
                raise UserError(_("NO INCOMING STOCK MOVE RECORD FOUND - UNABLE TO CLOSE CONTRACT"))
            stock_move.picking_id.sudo().message_post(body=message)

        # Now search for an analytic account for the serial number
        self.create_inverse_analytic_line(main_machine)
        self.unset_values_on_lot(main_machine)
        self.unlink_machine_on_contract(subscription)

        if not self.x_is_donate:
            main_machine.sudo().message_post(body=message)
        else:
            message = 'Contract :' + subscription.name + '\n Terminated ' + '\n Partner: ' + subscription.partner_id.name + '\n Serial No: ' + \
                      main_machine.name + '\n Reason: ' + self.close_reason_id.name + '\n Machine donated to client'
            main_machine.sudo().message_post(body=message)

        subscription.sudo().message_post(body=message)
        subscription.analytic_account_id.sudo().message_post(body=message)

        subscription.close_reason_id = self.close_reason_id
        subscription.set_close()
