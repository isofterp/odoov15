from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    x_task_id = fields.Many2one('project.task', 'Job Number')
    x_equipment_id = fields.Many2one('maintenance.equipment', 'Equipment',
                                     domain="[('partner_id','=', partner_id)]")
    x_branch_id = fields.Integer('Old Branch')

    def button_draft(self):
        # The user will set the Vendor Biil to Draft if they want to re allocate items purchased
        # This code will remove or update the Job accordingly
        task_custom_lines_obj = self.env['task.custom.lines']
        project_task_material_obj = self.env['project.task.material']
        # unlink materials from Jobprint('Task id=', self.id)
        for rec in self.line_ids:
            if rec.x_task_id.id:
                print(rec.name, rec.x_task_id.id)
                product = task_custom_lines_obj.search([
                    ('task_custom_id', '=', rec.x_task_id.id),
                    ('product_id', '=', rec.product_id.id),
                    ])
                if product:
                    if product.actual_qty == rec.quantity:
                        product.unlink()
                    else:
                        product.actual_qty -= rec.quantity
                        product.actual_price -= rec.price_unit * rec.quantity

                    print('found product',rec.name,rec.x_task_id.id,)

                material = project_task_material_obj.search([('task_id', '=', rec.x_task_id.id),
                                                             ('product_id','=',rec.product_id.id ),
                                                             ('quantity', '=', rec.quantity)])
                if material:
                    print('found material ', material.product_id.name,material.id)
                    material.unlink()

        return super(AccountMove, self).button_draft()

    # In order to send a notification to the channel, all the invoice/ vendor bill lines need to be checked
    # for the corresponding task/ job if it is on any line. If any are found post a message for each specific one

    def _send_message(self):
        for move in self:
            for line in move.invoice_line_ids:
                if line.x_task_id:
                    logging.warning("This line has a task associated with it - Send message to the channel %s", line.x_task_id.name)
                    channel_odoo_bot_users = '%s' % ('Field Service')
                    channel_obj = self.env['mail.channel']
                    channel_id = channel_obj.search([('name', 'like', channel_odoo_bot_users)])

                    if not channel_id:
                        logging.warning("Could not find channel!!!!!")
                        channel_id = channel_obj.create({
                            'name': channel_odoo_bot_users,
                            'email_send': False,
                            'channel_type': 'channel',
                            'public': 'private',
                            'channel_partner_ids': [(4, odoo_bot.partner_id.id), (4, employee.user_id.partner_id.id)]
                        })
                    try:
                        if move.move_type in ('in_invoice', 'in_refund'):
                            my_task = "[" + line.x_task_id.code + "] " + line.x_task_id.name
                            logging.warning("My Task is %s", my_task)
                            msg = (
                                """Vendor Bill {bill} created for task <strong>{task}</strong><br/>
                                <strong>Product</strong>: {product} <br/>
                                <strong>User</strong>: {user}
                                """.format(
                                    bill = move.name,
                                    task=my_task,
                                    product=line.product_id.product_tmpl_id.name + " " + line.product_id.product_tmpl_id.description,
                                    user=move.user_id.name,
                                )
                            )

                            logging.warning("Sending message to channel!!!!!! %s", msg)
                            channel_id.sudo().message_post(
                                subject="Vendor bill " + move.name + " created for Job " + my_task,
                                body="Vendor bill " + move.name + " created for Job " + my_task,
                                message_type='comment',
                                subtype_id=1,
                            )

                    except Exception as e:
                        print('ERROR in _send_message')

                    try:
                        line.x_task_id.message_post(body=msg)
                    except Exception as f:
                        logging.warning("Could not post message to task %s", line.x_task_id.name)

    # def action_post(self):
    #     if self._context.get('default_move_type') == 'out_invoice':
    #         return super(AccountMove, self).action_post()
    #
    #     #print('in action_post ',self.line_ids)
    #     task_custom_lines_obj = self.env['task.custom.lines']
    #     project_task_material_obj = self.env['project.task.material']
    #
    #
    #     for rec in self.line_ids:
    #         logging.warning("Is this code working!!!!!!!!!!!!")
    #         if rec.x_task_id and rec.x_project_id:
    #             #print(rec)
    #             if not rec.exclude_from_invoice_tab:
    #                 # print('in my action_post task id ', rec.name, rec.x_task_id.id)
    #                 custom_line = task_custom_lines_obj.search([('product_id', 'ilike', rec.product_id.id),
    #                                                             ('task_custom_id', '=', rec.x_task_id.id)])
    #                 if custom_line:
    #                     # print('found customer line', custom_line)
    #                     custom_line.actual_qty += rec.quantity
    #                     custom_line.actual_cost += rec.amount_residual
    #                     custom_line.actual_profit = custom_line.price - custom_line.actual_cost
    #                     # custom_line.actual_profit = custom_line.quoted_price - custom_line.actual_cost
    #
    #                 else:
    #                     if rec.x_task_id and rec.x_project_id:
    #                         # print("Working with line %s", rec.quantity)
    #                         vals = {  # Cant find record so create a quote line
    #                             'task_custom_id': rec.x_task_id.id,
    #                             'task_id': rec.x_task_id.id,
    #                             'product_id': rec.product_id.id,
    #                             'product_uom': rec.product_uom_id.id,
    #                             'qty': rec.quantity,
    #                             'total_cost': rec.quantity * rec.amount_residual,
    #                             'price': rec.quantity * rec.amount_residual,
    #                             'purchase_price': rec.amount_residual,
    #                             'unit_price': rec.amount_residual,
    #
    #                             'actual_qty': rec.quantity,
    #                             'actual_cost': rec.amount_residual,
    #                             'actual_profit': rec.quantity * rec.amount_residual *-1,
    #                             'notes': rec.name,
    #                         }
    #                         # print(vals)
    #                         new_line = task_custom_lines_obj.create(vals)
    #                         new_line.update_selling_from_other_source()
    #                         new_line._calculate_unit_price()
    #                         # print('we are here')
    #                         if new_line:
    #                             print("New line created")
    #                         else:
    #                             print("No task line created")
    #                 # Create a Material line
    #                 material = project_task_material_obj.search([('task_id', '=', rec.x_task_id.id),('product_id','=', rec.product_id.id)])
    #                 if material:
    #                     material.quantity = custom_line.actual_qty
    #                 else:
    #                     if rec.x_task_id and rec.x_project_id:
    #                         logging.warning("QTY is %s", rec.quantity)
    #                         vals = {
    #                             'task_id': rec.x_task_id.id,
    #                             'product_id': rec.product_id.id,
    #                             'quantity': rec.quantity,
    #                             'product_uom_id': 1,
    #                  line.price_unit           'ticked': True
    #                         }
    #                         #print(vals)
    #                         new_line = project_task_material_obj.create(vals)
    #
    #
    #             # print(rec.x_task_id.name, rec.product_id, rec.name)
    #     ~print(err)
    #     res =  super(AccountMove, self).action_post()
    #     self._send_message()
    #     return res

    @api.model
    def create(self, vals):
        """Overridden create method to update the lines."""
        new_move = super(AccountMove, self).create(vals)
        # print('VALS=  ',vals)
        # The below code sets all the move lines with the same branch
        # This has the issue in that everything on the vendor bill will be for the same branch which is not
        # necessarily wrong
        # The same however cannot be saud for the job number. Each line will have to have its own job number set

        if new_move and new_move.branch_id:
            print("in multi branch - standard @ around line 98")
            if new_move.line_ids:
                new_move.line_ids.write(
                    {"branch_id": new_move.branch_id and new_move.branch_id.id or False, }
                )

                # Get the invoice line ids from vals
                tmp_lines_list = vals.get('invoice_line_ids')
                # logging.warning("Lines in list is %s", tmp_lines_list[0])
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
                            if isinstance(tmp_line, dict):
                                logging.warning("The dict is %s", tmp_line)
                                # Find the move line rec in the new record that matches this line
                                inv_line = self.env['account.move.line'].search([('move_id', '=', new_move.id),
                                                                                 ('product_id', '=',
                                                                                  tmp_line.get('product_id')),
                                                                                 ('quantity', '=',
                                                                                  tmp_line.get('quantity')), ])
                                if inv_line:
                                    # logging.warning("Found line with ID %s", inv_line.id)
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

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        ''' Prepare values used to create the journal items (account.move.line) corresponding to the Cost of Good Sold
        lines (COGS) for customer invoices.

        Example:

        Buy a product having a cost of 9 being a storable product and having a perpetual valuation in FIFO.
        Sell this product at a price of 10. The customer invoice's journal entries looks like:

        Account                                     | Debit | Credit
        ---------------------------------------------------------------
        200000 Product Sales                        |       | 10.0
        ---------------------------------------------------------------
        101200 Account Receivable                   | 10.0  |
        ---------------------------------------------------------------

        This method computes values used to make two additional journal items:

        ---------------------------------------------------------------
        220000 Expenses                             | 9.0   |
        ---------------------------------------------------------------
        101130 Stock Interim Account (Delivered)    |       | 9.0
        ---------------------------------------------------------------

        Note: COGS are only generated for customer invoices except refund made to cancel an invoice.

        :return: A list of Python dictionary to be passed to env['account.move.line'].create.
        '''
        lines_vals_list = []
        for move in self:
            # Make the loop multi-company safe when accessing models like product.product
            move = move.with_company(move.company_id)

            if not move.is_sale_document(include_receipts=True) or not move.company_id.anglo_saxon_accounting:
                continue

            for line in move.invoice_line_ids:

                # Filter out lines being not eligible for COGS.
                if line.product_id.type != 'product' or line.product_id.valuation != 'real_time':
                    continue

                # Retrieve accounts needed to generate the COGS.
                accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=move.fiscal_position_id)
                debit_interim_account = accounts['stock_output']
                credit_expense_account = accounts['expense'] or move.journal_id.default_account_id
                if not debit_interim_account or not credit_expense_account:
                    continue

                # Compute accounting fields.
                sign = -1 if move.move_type == 'out_refund' else 1
                # If this line is linked to a job - fetch the cost price from the job
                if move.move_type == 'out_invoice' and line.move_id.x_task_id:
                    custom_line = self.env['task.custom.lines'].search(
                        [('task_custom_id', '=', line.move_id.x_task_id.id),
                         ('product_id', '=', line.product_id.id)])
                    if custom_line:
                        logging.warning("Line found is %s", custom_line.notes)
                        price_unit = custom_line.actual_cost
                        balance = sign * line.quantity * price_unit

                else:
                    price_unit = line._stock_account_get_anglo_saxon_price_unit()
                    balance = sign * line.quantity * price_unit

                # Add interim account line.
                lines_vals_list.append({
                    'name': line.name[:64],
                    'move_id': move.id,
                    'partner_id': move.commercial_partner_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity': line.quantity,
                    'price_unit': price_unit,
                    'debit': balance < 0.0 and -balance or 0.0,
                    'credit': balance > 0.0 and balance or 0.0,
                    'account_id': debit_interim_account.id,
                    'exclude_from_invoice_tab': True,
                    'is_anglo_saxon_line': True,
                })

                # Add expense account line.
                lines_vals_list.append({
                    'name': line.name[:64],
                    'move_id': move.id,
                    'partner_id': move.commercial_partner_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity': line.quantity,
                    'price_unit': -price_unit,
                    'debit': balance > 0.0 and balance or 0.0,
                    'credit': balance < 0.0 and -balance or 0.0,
                    'account_id': credit_expense_account.id,
                    'analytic_account_id': line.analytic_account_id.id,
                    'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                    'exclude_from_invoice_tab': True,
                    'is_anglo_saxon_line': True,
                })
        _logger.warning("Lines val List %s", lines_vals_list)
        # print(err)
        return lines_vals_list


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def create_analytic_lines(self):
        """ Create analytic items upon validation of an account.move.line having an analytic account or an analytic distribution.
        """
        lines_to_create_analytic_entries = self.env['account.move.line']
        analytic_line_vals = []
        job_id = ''
        for obj_line in self:
            for tag in obj_line.analytic_tag_ids.filtered('active_analytic_distribution'):
                for distribution in tag.analytic_distribution_ids:
                    analytic_line_vals.append(obj_line._prepare_analytic_distribution_line(distribution))
            if obj_line.analytic_account_id:
                lines_to_create_analytic_entries |= obj_line

        # create analytic entries in batch
        if lines_to_create_analytic_entries:
            analytic_line_vals += lines_to_create_analytic_entries._prepare_analytic_line()
        my_id = self.env['account.analytic.line'].create(analytic_line_vals)
        # Set the task_id on the analytic record after it has been created
        for rec in self:
            job_id = rec.move_id.x_task_id.id
        my_id.write({'task_id': job_id})

    @api.onchange('x_project_id')
    def onchange_x_project_id(self):

        if self.x_project_id:
            analytic_account = self.env["account.analytic.account"].search([("name", "=", self.x_project_id.name)])
            if analytic_account:
                self.analytic_account_id = analytic_account.id

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue

            #line.name = line._get_computed_name()
            line.name = line.product_id.code or line.product_id.name
            line.account_id = line._get_computed_account()
            taxes = line._get_computed_taxes()
            if taxes and line.move_id.fiscal_position_id:
                taxes = line.move_id.fiscal_position_id.map_tax(taxes, partner=line.partner_id)
            line.tax_ids = taxes
            line.product_uom_id = line._get_computed_uom()
            line.price_unit = line._get_computed_price_unit()

    # @api.onchange("x_project_id")
    # def _get_task_domain(self):
    #     if self.x_project_id:
    #         ids = self.env['project.task'].search([('project_id', '=', self.x_project_id.id)])
    #         task_list = self.env['project.task'].browse([ids])
    #         list = []
    #         for id in ids:
    #             list.append(id.id)
    #         print(list)
    #         #self.domain_field =  {[('id', 'in', list)]}
    #         self.domain_field = "[('id', 'in', " + str(list) + ")]"



            #print( self.domain_field)
            #return {ids[0]: [('id', 'in', list)]}

    # @api.onchange("x_project_id")
    # def populate_task(self):
    #     print('in my onchange x_project_id')
    #     task_ids = self.env['project.task'].search([('project_id','=',self.x_project_id.id)])
    #     print('equipment', task_ids)
    #     self.x_task_id = task_ids
    #     print('self.x_task_id ===',self.x_task_id)

    # @api.onchange("x_task_id")
    # def populate_equipment(self):
    #     # print('in my onchange x_task_id',)
    #     equipment = self.env['project.project'].search([('id', '=', self.x_task_id.project_id.id)])
    #     # print('equipment', equipment)
    #     self.x_project_id = equipment.id

    x_project_id = fields.Many2one('project.project', 'Equipment')
    x_task_id = fields.Many2one('project.task', 'Job Number')
    x_branch_id = fields.Integer('Old Branch')


    domain_field = fields.Char( string="Domain")
    #    domain_field = fields.Char(compute='_get_task_domain', string="Domain")

class AccountInvoiceSend(models.TransientModel):
    _inherit = "account.invoice.send"

    def _send_email(self):
        res = super(AccountInvoiceSend, self)._send_email()
        stage_id = self.env['project.task.type'].search([('name', 'like', 'Invoiced'), ('active', '=', True)])
        self.mapped('invoice_ids.x_task_id').sudo().write({'stage_id': stage_id.id})




